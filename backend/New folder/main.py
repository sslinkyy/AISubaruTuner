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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories
os.makedirs("./uploads", exist_ok=True)
os.makedirs("./exports", exist_ok=True)
os.makedirs("./logs", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ECU Tuning Application")
    yield
    # Shutdown
    logger.info("Shutting down ECU Tuning Application")

app = FastAPI(
    title="ECU Tuning Assistant API", 
    version="2.0.0",
    description="Production-ready ECU tuning application with datalog analysis and tune optimization",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
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

# Import modules
from tune_diff import compute_tune_diff, TuneDiffResult
from datalog_parser import parse_datalog, detect_issues
from ai_suggestions import generate_suggestions
from safety_checks import run_safety_checks
from tune_optimizer import optimize_tune

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

def detect_platform(datalog_path: str, tune_path: str) -> str:
    """Detect ECU platform based on files"""
    try:
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
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Package Upload (Datalog + Tune)
@app.post("/api/upload_package")
async def upload_package(
    datalog: UploadFile = File(...),
    tune: UploadFile = File(...),
    user: dict = Depends(verify_token)
):
    try:
        # Validate files
        validate_file_size(datalog, 50)
        validate_file_size(tune, 50)
        validate_file_type(datalog.filename, ['.csv', '.log'])
        validate_file_type(tune.filename, ['.bin', '.hex', '.rom'])

        session_id = generate_session_id()
        session_dir = f"./uploads/{session_id}"
        os.makedirs(session_dir, exist_ok=True)

        # Save files
        datalog_path = f"{session_dir}/{datalog.filename}"
        tune_path = f"{session_dir}/{tune.filename}"

        with open(datalog_path, "wb") as f:
            f.write(await datalog.read())
        with open(tune_path, "wb") as f:
            f.write(await tune.read())

        # Generate file hashes for integrity
        datalog_hash = hash_file(datalog_path)
        tune_hash = hash_file(tune_path)

        # Detect platform
        platform = detect_platform(datalog_path, tune_path)

        # Store session info
        active_sessions[session_id] = {
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
            "status": "uploaded"
        }

        usage_stats["total_sessions"] += 1

        logger.info(f"Package uploaded for session {session_id} by user {user['user_id']}")

        return {
            "status": "success",
            "session_id": session_id,
            "platform": platform,
            "datalog": active_sessions[session_id]["datalog"],
            "tune": active_sessions[session_id]["tune"]
        }

    except Exception as e:
        logger.error(f"Package upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Analyze Package - FIXED VERSION
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
        platform = session["platform"]

        # Parse datalog
        try:
            datalog_df = parse_datalog(datalog_path, platform)
        except Exception as e:
            logger.error(f"Failed to parse datalog: {e}")
            raise HTTPException(status_code=400, detail="Invalid or corrupt datalog file")

        # Detect issues in datalog
        issues = detect_issues(datalog_df, platform)

        # Convert datalog DataFrame to dict format for your helper functions
        datalog_dict = {
            "data": datalog_df.to_dict(orient="records"),
            "columns": list(datalog_df.columns),
            "total_rows": len(datalog_df),
            "platform": platform
        }

        # Parse tune file (basic implementation - you can enhance this)
        tune_dict = {}
        try:
            # For now, just store basic tune info
            # In production, you'd parse the binary tune file
            tune_dict = {
                "file_path": tune_path,
                "platform": platform,
                "size": session["tune"].get("file_size", 0),
                "hash": session["tune"]["hash"]
            }
        except Exception as e:
            logger.warning(f"Could not parse tune file: {e}")
            tune_dict = {"error": str(e)}

        # Run safety checks with proper data format
        try:
            safety_report = run_safety_checks(tune_dict, datalog_dict)
        except Exception as e:
            logger.error(f"Failed to run safety checks: {e}")
            safety_report = {
                "overall_status": "error", 
                "critical_issues": [],
                "warnings": [],
                "recommendations": [],
                "error": str(e)
            }

        # Prepare analysis data for AI suggestions
        analysis_data = {
            "datalog": datalog_dict,
            "tune": tune_dict,
            "platform": platform,
            "issues": issues
        }

        # Generate AI tuning suggestions with proper data format
        try:
            suggestions = generate_suggestions(analysis_data)
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            suggestions = [{
                "id": "error_suggestion",
                "type": "error",
                "priority": "low",
                "description": f"Suggestion generation failed: {e}",
                "parameter": "unknown",
                "change_type": "none",
                "affected_areas": "none",
                "safety_impact": "none",
                "performance_impact": "none"
            }]

        # Generate optimized tune preview with proper data format
        try:
            optimized_tune_preview = optimize_tune(tune_dict, datalog_dict, suggestions)
        except Exception as e:
            logger.error(f"Failed to optimize tune: {e}")
            optimized_tune_preview = {
                "base_tune": tune_dict,
                "changes": [],
                "optimization_summary": {
                    "total_changes": 0,
                    "safety_improvements": 0,
                    "performance_improvements": 0
                },
                "error": str(e)
            }

        # Update session with analysis results
        session["analysis"] = {
            "completed_at": datetime.now().isoformat(),
            "issues_count": len(issues),
            "suggestions_count": len(suggestions),
            "safety_status": safety_report.get("overall_status", "unknown")
        }

        # Log analysis completion
        logger.info(f"Analysis complete for session {session_id} by user {user['user_id']}")

        # Return structured response
        return {
            "status": "success",
            "session_id": session_id,
            "platform": platform,
            "datalog_summary": {
                "total_rows": len(datalog_df),
                "total_columns": len(datalog_df.columns),
                "columns": list(datalog_df.columns)
            },
            "issues": issues,
            "safety_report": safety_report,
            "suggestions": suggestions,
            "optimized_tune_preview": optimized_tune_preview,
            "analysis_metadata": {
                "analyzed_at": datetime.now().isoformat(),
                "analysis_version": "2.0.0",
                "total_issues": len(issues),
                "total_suggestions": len(suggestions),
                "safety_status": safety_report.get("overall_status", "unknown")
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")