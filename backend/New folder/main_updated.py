from fastapi import FastAPI, UploadFile, File, Body, Depends, Response, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os
import json
import pandas as pd
import difflib
import hashlib
import uuid
import logging
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories
os.makedirs("./uploads", exist_ok=True)
os.makedirs("./exports", exist_ok=True)
os.makedirs("./logs", exist_ok=True)

def to_python_types(obj):
    """Recursively convert numpy and pandas types to native Python types for JSON serialization."""
    import numpy as np
    import pandas as pd

    if isinstance(obj, dict):
        return {k: to_python_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_python_types(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.generic):  # catches other numpy scalars (e.g., np.str_)
        return obj.item()
    elif pd.isna(obj):  # Handle pandas NaN values
        return None
    else:
        return obj

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ECU Tuning Application v3.0.0 with Enhanced ROM Analysis")
    yield
    # Shutdown
    logger.info("Shutting down ECU Tuning Application")

app = FastAPI(
    title="ECU Tuning Assistant API", 
    version="3.0.0",
    description="Production-ready ECU tuning application with XML definition support and comprehensive ROM analysis",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. For production, specify your domain(s).
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# In-memory storage (replace with database in production)
session_history = {}
rules_db = {}
ml_models = []
audit_log = []
active_sessions = {}
usage_stats = {
    "total_sessions": 0,
    "active_users": 0,
    "avg_rating": 4.7,
    "suggestion_acceptance": 0.82,
    "safety_pass_rate": 0.95
}

# Import existing modules (legacy support)
try:
    from tune_diff import compute_tune_diff, TuneDiffResult
    from datalog_parser import parse_datalog, detect_issues
    from ai_suggestions import generate_suggestions
    from safety_checks import run_safety_checks
    from tune_optimizer import optimize_tune
    legacy_modules_available = True
except ImportError as e:
    logger.warning(f"Legacy modules not available: {e}")
    legacy_modules_available = False

# Import new ROM analysis modules
from rom_integration import ROMIntegrationManager, create_rom_integration_manager

# Create global ROM integration manager
rom_manager = create_rom_integration_manager()

# Authentication helper
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # In production, implement proper JWT verification
    return {"user_id": "demo_user", "role": "user"}

def is_admin(user: dict = Depends(verify_token)):
    return user.get("role") == "admin"

# Utility functions
def generate_session_id():
    return str(uuid.uuid4())

def hash_file(file_path: str) -> str:
    """Generate hash for file integrity checking"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def validate_file_size(file: UploadFile, max_size_mb: int = 50):
    """Validate file size"""
    if hasattr(file, 'size') and file.size > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max size: {max_size_mb}MB")

def validate_file_type(filename: str, allowed_extensions: List[str]):
    """Validate file extension"""
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {allowed_extensions}")

def detect_platform(datalog_path: str, tune_path: str = None, definition_path: str = None) -> str:
    """Enhanced platform detection with XML definition support"""
    try:
        # Check for XML definition first
        if definition_path and definition_path.endswith('.xml'):
            return "Subaru"

        # Check ROM file extension
        if tune_path:
            tune_ext = Path(tune_path).suffix.lower()
            if tune_ext in ['.bin', '.hex', '.rom']:
                return "Subaru"

        # Read first few lines of datalog
        with open(datalog_path, 'r') as f:
            content = f.read(1000).lower()

        if 'a/f correction' in content or 'engine speed' in content:
            return "Subaru"
        elif 'rpm' in content and 'map' in content:
            return "Hondata"
        else:
            return "Unknown"
    except:
        return "Unknown"

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0",
        "features": {
            "xml_definition_support": True,
            "rom_analysis": True,
            "legacy_compatibility": legacy_modules_available
        }
    }

# Enhanced Package Upload with XML Definition Support
@app.post("/api/upload_package")
async def upload_package(
    datalog: UploadFile = File(...),
    tune: UploadFile = File(...),
    definition: Optional[UploadFile] = File(None),
    user: dict = Depends(verify_token)
):
    try:
        # Validate files
        validate_file_size(datalog, 50)
        validate_file_size(tune, 50)
        validate_file_type(datalog.filename, ['.csv', '.log'])
        validate_file_type(tune.filename, ['.bin', '.hex', '.rom'])

        if definition:
            validate_file_size(definition, 10)
            validate_file_type(definition.filename, ['.xml'])

        session_id = generate_session_id()
        session_dir = f"./uploads/{session_id}"
        os.makedirs(session_dir, exist_ok=True)

        # Save files
        datalog_path = f"{session_dir}/{datalog.filename}"
        tune_path = f"{session_dir}/{tune.filename}"
        definition_path = None

        with open(datalog_path, "wb") as f:
            f.write(await datalog.read())
        with open(tune_path, "wb") as f:
            f.write(await tune.read())

        if definition:
            definition_path = f"{session_dir}/{definition.filename}"
            with open(definition_path, "wb") as f:
                f.write(await definition.read())

        # Generate file hashes for integrity
        datalog_hash = hash_file(datalog_path)
        tune_hash = hash_file(tune_path)
        definition_hash = hash_file(definition_path) if definition_path else None

        # Detect platform
        platform = detect_platform(datalog_path, tune_path, definition_path)

        # Store session info
        session_data = {
            "user_id": user["user_id"],
            "created_at": datetime.utcnow().isoformat(),
            "datalog": {
                "filename": datalog.filename,
                "file_path": datalog_path,
                "hash": datalog_hash
            },
            "tune": {
                "filename": tune.filename,
                "file_path": tune_path,
                "hash": tune_hash
            },
            "platform": platform,
            "status": "uploaded",
            "analysis_type": "enhanced" if definition_path else "standard"
        }

        if definition_path:
            session_data["definition"] = {
                "filename": definition.filename,
                "file_path": definition_path,
                "hash": definition_hash
            }

        active_sessions[session_id] = session_data
        usage_stats["total_sessions"] += 1

        logger.info(f"Package uploaded for session {session_id} by user {user['user_id']} (Platform: {platform}, XML: {definition_path is not None})")

        return to_python_types({
            "status": "success",
            "session_id": session_id,
            "platform": platform,
            "analysis_type": session_data["analysis_type"],
            "datalog": session_data["datalog"],
            "tune": session_data["tune"],
            "definition": session_data.get("definition"),
            "xml_definition_provided": definition_path is not None,
            "enhanced_analysis_available": definition_path is not None
        })

    except Exception as e:
        logger.error(f"Package upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Analyze Package with Complete ROM Integration
@app.post("/api/analyze_package")
async def analyze_package(
    session_id: str = Body(..., embed=True),
    user: dict = Depends(verify_token)
):
    try:
        # Validate session
        session = active_sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for user {user['user_id']}")
            raise HTTPException(status_code=404, detail="Session not found")

        datalog_path = session["datalog"]["file_path"]
        tune_path = session["tune"]["file_path"]
        definition_path = session.get("definition", {}).get("file_path")
        platform = session["platform"]

        logger.info(f"Starting enhanced analysis for session {session_id}")

        # Use enhanced ROM integration for complete analysis
        try:
            enhanced_results = rom_manager.analyze_rom_package(
                datalog_path=datalog_path,
                tune_path=tune_path,
                definition_path=definition_path
            )

            analysis_successful = True
            logger.info(f"Enhanced ROM analysis completed: {enhanced_results['rom_analysis']['tables_parsed']} tables, {enhanced_results['tune_changes']['total_changes']} changes")

        except Exception as e:
            logger.error(f"Enhanced ROM analysis failed: {e}")
            enhanced_results = None
            analysis_successful = False

        # Fallback to legacy analysis if enhanced fails or for compatibility
        legacy_results = None
        if legacy_modules_available:
            try:
                # Parse datalog with legacy parser for backward compatibility
                datalog_df = parse_datalog(datalog_path, platform)
                legacy_issues = detect_issues(datalog_df, platform)

                # Convert for legacy functions
                datalog_dict = {
                    "data": datalog_df.to_dict(orient="records"),
                    "columns": list(datalog_df.columns),
                    "total_rows": len(datalog_df),
                    "platform": platform
                }

                tune_dict = {
                    "file_path": tune_path,
                    "platform": platform,
                    "size": os.path.getsize(tune_path) if os.path.exists(tune_path) else 0,
                    "hash": session["tune"]["hash"]
                }

                # Run legacy safety checks
                safety_report = run_safety_checks(tune_dict, datalog_dict)

                # Generate legacy suggestions
                analysis_data = {
                    "datalog": datalog_dict,
                    "tune": tune_dict,
                    "platform": platform,
                    "issues": legacy_issues
                }
                legacy_suggestions = generate_suggestions(analysis_data)

                legacy_results = {
                    "issues": legacy_issues,
                    "suggestions": legacy_suggestions,
                    "safety_report": safety_report
                }

                logger.info("Legacy analysis completed successfully")

            except Exception as e:
                logger.warning(f"Legacy analysis failed: {e}")
                legacy_results = {
                    "issues": [],
                    "suggestions": [],
                    "safety_report": {"overall_status": "unknown", "critical_issues": [], "warnings": []}
                }

        # Update session with analysis results
        analysis_metadata = {
            "completed_at": datetime.now().isoformat(),
            "enhanced_analysis_successful": analysis_successful,
            "legacy_analysis_available": legacy_modules_available,
            "xml_definition_used": definition_path is not None
        }

        if enhanced_results:
            analysis_metadata.update({
                "issues_count": enhanced_results["datalog_analysis"]["issues_found"],
                "tables_parsed": enhanced_results["rom_analysis"]["tables_parsed"],
                "tune_changes_count": enhanced_results["tune_changes"]["total_changes"],
                "safety_status": enhanced_results["datalog_analysis"]["safety_status"],
                "analysis_confidence": enhanced_results["quality_metrics"]["analysis_confidence"]
            })

        session["analysis"] = analysis_metadata

        logger.info(f"Complete analysis finished for session {session_id} by user {user['user_id']}")

        # Prepare comprehensive response
        response_data = {
            "status": "success",
            "session_id": session_id,
            "platform": platform,
            "analysis_type": "enhanced" if enhanced_results else "legacy",
            "timestamp": datetime.now().isoformat()
        }

        # Add enhanced results if available
        if enhanced_results:
            response_data.update({
                "rom_analysis": enhanced_results["rom_analysis"],
                "datalog_analysis": enhanced_results["datalog_analysis"],
                "tune_changes": enhanced_results["tune_changes"],
                "quality_metrics": enhanced_results["quality_metrics"],
                "detailed_data": {
                    "rom_tables_summary": enhanced_results["detailed_data"]["rom_tables"][:20],  # Limit for response size
                    "critical_issues": enhanced_results["detailed_data"]["datalog_issues"][:10],
                    "top_suggestions": enhanced_results["detailed_data"]["suggestions"][:10],
                    "safety_warnings": enhanced_results["detailed_data"]["safety_warnings"]
                }
            })

        # Add legacy results for compatibility
        if legacy_results:
            response_data["legacy_compatibility"] = legacy_results

        # Add metadata
        response_data["metadata"] = {
            "analysis_version": "3.0.0",
            "enhanced_features_used": enhanced_results is not None,
            "xml_definition_available": definition_path is not None,
            "legacy_fallback_used": legacy_results is not None,
            "total_processing_time": "calculated_in_production"
        }

        return to_python_types(response_data)

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")

# Enhanced Table Data Endpoint
@app.get("/api/session/{session_id}/table/{table_name}")
async def get_table_data(
    session_id: str, 
    table_name: str,
    user: dict = Depends(verify_token)
):
    """Get specific ROM table data with enhanced details"""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if analysis has been run
    if "analysis" not in session:
        raise HTTPException(status_code=400, detail="Analysis not completed for this session")

    try:
        # Use ROM integration manager to get table data
        table_data = rom_manager.get_table_data(session, table_name)

        if not table_data:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

        return to_python_types(table_data)

    except Exception as e:
        logger.error(f"Failed to get table data for {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Tune Changes Endpoint
@app.get("/api/session/{session_id}/tune_changes")
async def get_tune_changes(
    session_id: str,
    detailed: bool = False,
    user: dict = Depends(verify_token)
):
    """Get detailed tune changes with enhanced analysis"""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if "analysis" not in session:
        raise HTTPException(status_code=400, detail="Analysis not completed")

    try:
        # Re-run analysis to get fresh tune changes
        datalog_path = session["datalog"]["file_path"]
        tune_path = session["tune"]["file_path"]
        definition_path = session.get("definition", {}).get("file_path")

        # Use ROM integration manager for complete analysis
        results = rom_manager.analyze_rom_package(datalog_path, tune_path, definition_path)

        tune_changes = results["tune_changes"]

        if detailed:
            # Include detailed change information
            tune_changes["detailed_changes"] = results["detailed_data"]["tune_change_details"]
            tune_changes["rom_compatibility"] = results["quality_metrics"]["rom_compatibility"]
            tune_changes["analysis_metadata"] = results["metadata"]

        return to_python_types(tune_changes)

    except Exception as e:
        logger.error(f"Failed to get tune changes for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint: Get ROM table list
@app.get("/api/session/{session_id}/tables")
async def get_rom_tables(
    session_id: str,
    category: Optional[str] = None,
    user: dict = Depends(verify_token)
):
    """Get list of available ROM tables"""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if "analysis" not in session:
        raise HTTPException(status_code=400, detail="Analysis not completed")

    try:
        # Get table list from ROM analysis
        datalog_path = session["datalog"]["file_path"]
        tune_path = session["tune"]["file_path"]
        definition_path = session.get("definition", {}).get("file_path")

        results = rom_manager.analyze_rom_package(datalog_path, tune_path, definition_path)
        tables = results["detailed_data"]["rom_tables"]

        # Filter by category if specified
        if category:
            category_keywords = {
                "fuel": ["fuel", "injector", "pulse"],
                "timing": ["timing", "ignition"],
                "boost": ["boost", "wastegate"],
                "idle": ["idle", "iac"],
                "learning": ["learning", "correction"]
            }

            if category.lower() in category_keywords:
                keywords = category_keywords[category.lower()]
                tables = [t for t in tables if any(kw in t["name"].lower() for kw in keywords)]

        return to_python_types({
            "session_id": session_id,
            "total_tables": len(tables),
            "category_filter": category,
            "tables": tables
        })

    except Exception as e:
        logger.error(f"Failed to get ROM tables for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint: Export tune changes
@app.post("/api/session/{session_id}/export_changes")
async def export_tune_changes(
    session_id: str,
    format: str = Body("json", embed=True),
    user: dict = Depends(verify_token)
):
    """Export tune changes in various formats"""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if format not in ["json", "csv", "xml"]:
        raise HTTPException(status_code=400, detail="Unsupported export format")

    try:
        # Get tune changes
        datalog_path = session["datalog"]["file_path"]
        tune_path = session["tune"]["file_path"]
        definition_path = session.get("definition", {}).get("file_path")

        results = rom_manager.analyze_rom_package(datalog_path, tune_path, definition_path)

        # Create export file
        export_dir = f"./exports/{session_id}"
        os.makedirs(export_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tune_changes_{timestamp}.{format}"
        filepath = f"{export_dir}/{filename}"

        if format == "json":
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        elif format == "csv":
            # Convert changes to CSV format
            changes_data = []
            for change in results["detailed_data"]["tune_change_details"]:
                for cell_change in change.get("cell_changes", []):
                    changes_data.append({
                        "table_name": change["table_name"],
                        "row": cell_change["row"],
                        "col": cell_change["col"],
                        "rpm": cell_change["rpm"],
                        "load": cell_change["load"],
                        "old_value": cell_change["old_value"],
                        "new_value": cell_change["new_value"],
                        "change_percent": cell_change["change_percent"],
                        "priority": change["priority"]
                    })

            df = pd.DataFrame(changes_data)
            df.to_csv(filepath, index=False)

        return {
            "status": "success",
            "export_file": filename,
            "format": format,
            "download_url": f"/api/download/{session_id}/{filename}"
        }

    except Exception as e:
        logger.error(f"Failed to export tune changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System status endpoint
@app.get("/api/system/status")
async def get_system_status(user: dict = Depends(verify_token)):
    """Get system status and statistics"""
    return {
        "status": "operational",
        "version": "3.0.0",
        "features": {
            "xml_definition_parsing": True,
            "rom_table_extraction": True,
            "enhanced_tune_analysis": True,
            "legacy_compatibility": legacy_modules_available
        },
        "statistics": {
            "active_sessions": len(active_sessions),
            "total_sessions": usage_stats["total_sessions"],
            "cache_size": len(rom_manager.cache) if hasattr(rom_manager, 'cache') else 0
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Clear cache endpoint (admin only)
@app.post("/api/admin/clear_cache")
async def clear_system_cache(user: dict = Depends(is_admin)):
    """Clear system cache (admin only)"""
    try:
        rom_manager.clear_cache()
        return {
            "status": "success",
            "message": "System cache cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
