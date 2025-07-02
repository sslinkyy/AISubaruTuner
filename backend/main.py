from fastapi import FastAPI, UploadFile, File, Body, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from datetime import datetime, timezone
import os
import json
import uuid
import logging
import pandas as pd
from pathlib import Path

if __package__ in {None, ""}:
    # Allow running this file directly via `python backend/main.py`
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "backend"

# Import project modules with fallbacks for direct execution
try:
    from .tune_diff import compute_tune_diff, TuneDiffResult
    from .datalog_parser import parse_datalog, detect_issues
    from .ai_suggestions import generate_suggestions
    from .safety_checks import run_safety_checks
    from .tune_optimizer import optimize_tune

    from backend.tune_diff import compute_tune_diff, TuneDiffResult
    from backend.datalog_parser import parse_datalog, detect_issues
    from backend.ai_suggestions import generate_suggestions
    from backend.safety_checks import run_safety_checks
    from backend.tune_optimizer import optimize_tune
    legacy_modules_available = True
except ImportError:
    try:
        from .tune_diff import compute_tune_diff, TuneDiffResult
        from .datalog_parser import parse_datalog, detect_issues
        from .ai_suggestions import generate_suggestions
        from .safety_checks import run_safety_checks
        from .tune_optimizer import optimize_tune
        legacy_modules_available = True
    except ImportError as e:
        logging.warning(f"Legacy modules not available: {e}")
        legacy_modules_available = False

from .rom_integration import create_rom_integration_manager
from . import enhanced_ai_suggestions
try:
    from backend.rom_integration import create_rom_integration_manager
except ImportError:
    from .rom_integration import create_rom_integration_manager

try:
    from backend import enhanced_ai_suggestions
except Exception:  # pragma: no cover - fallback for direct execution
    from . import enhanced_ai_suggestions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories
os.makedirs("./uploads", exist_ok=True)
os.makedirs("./exports", exist_ok=True)
os.makedirs("./logs", exist_ok=True)

app = FastAPI(
    title="ECU Tuning Assistant API",
    version="3.0.0",
    description="Production-ready ECU tuning application with XML definition support and comprehensive ROM analysis",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
rom_manager = create_rom_integration_manager()
active_sessions = {}
usage_stats = {
    "total_sessions": 0,
    "active_users": 0,
    "avg_rating": 4.7,
    "suggestion_acceptance": 0.82,
    "safety_pass_rate": 0.95,
}


def to_python_types(obj):
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
    elif isinstance(obj, np.generic):
        return obj.item()
    elif pd.isna(obj):
        return None
    else:
        return obj



# Authentication disabled

def verify_token() -> Dict[str, str]:
    """Return a default user without performing authentication."""
    return {"user_id": "anonymous", "role": "admin"}

def is_admin() -> bool:
    """Simplified admin check when authentication is disabled."""
    return True






def generate_session_id():
    return str(uuid.uuid4())


def hash_file(file_path: str) -> str:
    import hashlib

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_file_size(file: UploadFile, max_size_mb: int = 50):
    if hasattr(file, "size") and file.size > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413, detail=f"File too large. Max size: {max_size_mb}MB"
        )


def validate_file_type(filename: str, allowed_extensions: List[str]):
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail=f"Invalid file type. Allowed: {allowed_extensions}"
        )
def detect_platform(
    datalog_path: str, tune_path: str = None, definition_path: str = None
) -> str:
    try:
        if definition_path and definition_path.endswith(".xml"):
            return "Subaru"
        if tune_path:
            tune_ext = Path(tune_path).suffix.lower()
            if tune_ext in [".bin", ".hex", ".rom"]:
                return "Subaru"
        with open(datalog_path, "r") as f:
            content = f.read(1000).lower()
        if "a/f correction" in content or "engine speed" in content:
            return "Subaru"
        elif "rpm" in content and "map" in content:
            return "Hondata"
        else:
            return "Unknown"
    except:
        return "Unknown"


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "3.0.0",
        "features": {
            "xml_definition_support": True,
            "rom_analysis": True,
            "legacy_compatibility": legacy_modules_available,
        },
    }


@app.post("/api/upload_package")
async def upload_package(
    datalog: UploadFile = File(...),
    tune: UploadFile = File(...),
    definition: Optional[UploadFile] = File(None),
    user: dict = Depends(verify_token),
):
    try:
        validate_file_size(datalog, 50)
        validate_file_size(tune, 50)
        validate_file_type(datalog.filename, [".csv", ".log"])
        validate_file_type(tune.filename, [".bin", ".hex", ".rom"])
        if definition:
            validate_file_size(definition, 10)
            validate_file_type(definition.filename, [".xml"])

        session_id = generate_session_id()
        session_dir = f"./uploads/{session_id}"
        os.makedirs(session_dir, exist_ok=True)

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

        datalog_hash = hash_file(datalog_path)
        tune_hash = hash_file(tune_path)
        definition_hash = hash_file(definition_path) if definition_path else None

        platform = detect_platform(datalog_path, tune_path, definition_path)

        session_data = {
            "user_id": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "datalog": {
                "filename": datalog.filename,
                "file_path": datalog_path,
                "hash": datalog_hash,
            },
            "tune": {
                "filename": tune.filename,
                "file_path": tune_path,
                "hash": tune_hash,
            },
            "platform": platform,
            "status": "uploaded",
            "analysis_type": "enhanced" if definition_path else "standard",
        }
        if definition_path:
            session_data["definition"] = {
                "filename": definition.filename,
                "file_path": definition_path,
                "hash": definition_hash,
            }

        active_sessions[session_id] = session_data
        usage_stats["total_sessions"] += 1

        logger.info(
            f"Package uploaded for session {session_id} by user {user['user_id']} (Platform: {platform}, XML: {definition_path is not None})"
        )

        return to_python_types(
            {
                "status": "success",
                "session_id": session_id,
                "platform": platform,
                "analysis_type": session_data["analysis_type"],
                "datalog": session_data["datalog"],
                "tune": session_data["tune"],
                "definition": session_data.get("definition"),
                "xml_definition_provided": definition_path is not None,
                "enhanced_analysis_available": definition_path is not None,
            }
        )

    except Exception as e:
        logger.error(f"Package upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze_package")
async def analyze_package(
    session_id: str = Body(..., embed=True), user: dict = Depends(verify_token)
):
    try:
        session = active_sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for user {user['user_id']}")
            raise HTTPException(status_code=404, detail="Session not found")

        datalog_path = session["datalog"]["file_path"]
        tune_path = session["tune"]["file_path"]
        definition_path = session.get("definition", {}).get("file_path")
        platform = session["platform"]

        logger.info(f"Starting enhanced analysis for session {session_id}")

        enhanced_results = None
        analysis_successful = False
        try:
            enhanced_results = rom_manager.analyze_rom_package(
                datalog_path=datalog_path,
                tune_path=tune_path,
                definition_path=definition_path,
            )
            analysis_successful = True
            logger.info(
                f"Enhanced ROM analysis completed: {enhanced_results['rom_analysis']['tables_parsed']} tables, {enhanced_results['tune_changes']['total_changes']} changes"
            )
        except Exception as e:
            logger.error(f"Enhanced ROM analysis failed: {e}")
            enhanced_results = None
            analysis_successful = False

        # --- DEBUGGING AND DATALOG INJECTION START ---
        if enhanced_results:
            datalog_analysis = enhanced_results.get("datalog_analysis", {})
            logger.info(f"Datalog analysis keys: {list(datalog_analysis.keys())}")
            datalog_data = datalog_analysis.get("datalog", {}).get("data", [])
            logger.info(f"Datalog data length: {len(datalog_data)}")

            if not datalog_data:
                logger.info(
                    "Datalog data missing or empty, parsing datalog manually..."
                )
                datalog_df = parse_datalog(datalog_path, platform)
                datalog_records = datalog_df.to_dict(orient="records")
                enhanced_results.setdefault("datalog_analysis", {}).setdefault(
                    "datalog", {}
                )["data"] = datalog_records

                da_summary = {
                    "total_rows": len(datalog_df),
                    "total_columns": len(datalog_df.columns),
                }
                if "Time (msec)" in datalog_df.columns and len(datalog_df) > 1:
                    da_summary["duration"] = (
                        datalog_df["Time (msec)"].iloc[-1] - datalog_df["Time (msec)"].iloc[0]
                    ) / 1000.0
                enhanced_results.setdefault("datalog_analysis", {}).setdefault(
                    "datalog", {}
                )["data"] = datalog_records
                enhanced_results["datalog_analysis"].setdefault("summary", {}).update(da_summary)

                enhanced_results.setdefault("datalog_analysis", {}).setdefault(
                    "datalog", {}
                )["data"] = datalog_records

                logger.info(
                    f"Injected {len(datalog_records)} datalog records into analysis results"
                )
        # --- DEBUGGING AND DATALOG INJECTION END ---

        legacy_results = None
        if legacy_modules_available:
            try:
                datalog_df = parse_datalog(datalog_path, platform)
                legacy_issues = detect_issues(datalog_df, platform)

                datalog_dict = {
                    "data": datalog_df.to_dict(orient="records"),
                    "columns": list(datalog_df.columns),
                    "total_rows": len(datalog_df),
                    "platform": platform,
                }

                tune_dict = {
                    "file_path": tune_path,
                    "platform": platform,
                    "size": (
                        os.path.getsize(tune_path) if os.path.exists(tune_path) else 0
                    ),
                    "hash": session["tune"]["hash"],
                }

                safety_report = run_safety_checks(tune_dict, datalog_dict)

                analysis_data = {
                    "datalog": datalog_dict,
                    "tune": tune_dict,
                    "platform": platform,
                    "issues": legacy_issues,
                }
                legacy_suggestions = generate_suggestions(analysis_data)

                legacy_results = {
                    "issues": legacy_issues,
                    "suggestions": legacy_suggestions,
                    "safety_report": safety_report,
                }

                logger.info("Legacy analysis completed successfully")

            except Exception as e:
                logger.warning(f"Legacy analysis failed: {e}")
                legacy_results = {
                    "issues": [],
                    "suggestions": [],
                    "safety_report": {
                        "overall_status": "unknown",
                        "critical_issues": [],
                        "warnings": [],
                    },
                }

        ai_suggestions_list = []
        if enhanced_results:
            try:
                ai_suggestions_list = (
                    enhanced_ai_suggestions.generate_enhanced_ai_suggestions(
                        {
                            "datalog": enhanced_results.get("datalog_analysis", {}),
                            "datalog": enhanced_results.get("datalog_analysis", {}).get(
                                "datalog", {}
                            ),
                            "tune": enhanced_results.get("tune_changes", {}),
                            "platform": platform,
                            "issues": enhanced_results.get("datalog_analysis", {}).get(
                                "issues", []
                            ),
                        }
                    )
                )
            except Exception as e:
                logger.error(f"Failed to generate enhanced AI suggestions: {e}")
                ai_suggestions_list = []

        analysis_metadata = {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "enhanced_analysis_successful": analysis_successful,
            "legacy_analysis_available": legacy_modules_available,
            "xml_definition_used": definition_path is not None,
        }

        if enhanced_results:
            analysis_metadata.update(
                {
                    "issues_count": enhanced_results["datalog_analysis"].get(
                        "issues_found", 0
                    ),
                    "tables_parsed": enhanced_results["rom_analysis"].get(
                        "tables_parsed", 0
                    ),
                    "tune_changes_count": enhanced_results["tune_changes"].get(
                        "total_changes", 0
                    ),
                    "safety_status": enhanced_results["datalog_analysis"].get(
                        "safety_status", "unknown"
                    ),
                    "analysis_confidence": enhanced_results["quality_metrics"].get(
                        "analysis_confidence", 0
                    ),
                }
            )

        session["analysis"] = analysis_metadata

        logger.info(
            f"Complete analysis finished for session {session_id} by user {user['user_id']}"
        )

        response_data = {
            "status": "success",
            "session_id": session_id,
            "platform": platform,
            "analysis_type": "enhanced" if enhanced_results else "legacy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ai_suggestions": ai_suggestions_list,
        }

        if enhanced_results:
            response_data.update(
                {
                    "rom_analysis": enhanced_results["rom_analysis"],
                    "datalog_analysis": enhanced_results["datalog_analysis"],
                    "tune_changes": enhanced_results["tune_changes"],
                    "quality_metrics": enhanced_results["quality_metrics"],
                    "detailed_data": {
                        "rom_tables_summary": enhanced_results["detailed_data"][
                            "rom_tables"
                        ][:20],
                        "critical_issues": enhanced_results["detailed_data"][
                            "datalog_issues"
                        ][:10],
                        "top_suggestions": enhanced_results["detailed_data"][
                            "suggestions"
                        ][:10],
                        "safety_warnings": enhanced_results["detailed_data"][
                            "safety_warnings"
                        ],
                    },
                }
            )

        if legacy_results:
            response_data["legacy_compatibility"] = legacy_results

        response_data["metadata"] = {
            "analysis_version": "3.0.0",
            "enhanced_features_used": enhanced_results is not None,
            "xml_definition_available": definition_path is not None,
            "legacy_fallback_used": legacy_results is not None,
            "total_processing_time": "calculated_in_production",
        }

        return to_python_types(response_data)

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error during analysis"
        )


# ... (rest of your endpoints unchanged) ...


@app.get("/api/session/{session_id}/table/{table_name}")
async def get_table_data(
    session_id: str, table_name: str, user: dict = Depends(verify_token)
):
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if "analysis" not in session:
        raise HTTPException(
            status_code=400, detail="Analysis not completed for this session"
        )

    try:
        table_data = rom_manager.get_table_data(session, table_name)
        if not table_data:
            raise HTTPException(
                status_code=404, detail=f"Table '{table_name}' not found"
            )
        return to_python_types(table_data)
    except Exception as e:
        logger.error(f"Failed to get table data for {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}/table_diff/{table_name}")
async def get_table_diff(
    session_id: str, table_name: str, user: dict = Depends(verify_token)
):
    """Return before/after values for a ROM table in Carberry format"""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if "analysis" not in session:
        raise HTTPException(status_code=400, detail="Analysis not completed")

    try:
        datalog_path = session["datalog"]["file_path"]
        tune_path = session["tune"]["file_path"]
        definition_path = session.get("definition", {}).get("file_path")

        results = rom_manager.analyze_rom_package(
            datalog_path, tune_path, definition_path
        )
        tune_changes = results["detailed_data"]["tune_change_details"]

        table_data = rom_manager.get_table_data(session, table_name)
        if not table_data:
            raise HTTPException(
                status_code=404, detail=f"Table '{table_name}' not found"
            )

        diff = rom_manager.generate_carberry_diff(table_data, tune_changes)
        return to_python_types(diff)
    except Exception as e:
        logger.error(f"Failed to get table diff for {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}/tune_changes")
async def get_tune_changes(
    session_id: str, detailed: bool = False, user: dict = Depends(verify_token)
):
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if "analysis" not in session:
        raise HTTPException(status_code=400, detail="Analysis not completed")

    try:
        datalog_path = session["datalog"]["file_path"]
        tune_path = session["tune"]["file_path"]
        definition_path = session.get("definition", {}).get("file_path")

        results = rom_manager.analyze_rom_package(
            datalog_path, tune_path, definition_path
        )
        tune_changes = results["tune_changes"]

        if detailed:
            tune_changes["detailed_changes"] = results["detailed_data"][
                "tune_change_details"
            ]
            tune_changes["rom_compatibility"] = results["quality_metrics"][
                "rom_compatibility"
            ]
            tune_changes["analysis_metadata"] = results["metadata"]

        return to_python_types(tune_changes)
    except Exception as e:
        logger.error(f"Failed to get tune changes for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}/tables")
async def get_rom_tables(
    session_id: str, category: Optional[str] = None, user: dict = Depends(verify_token)
):
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if "analysis" not in session:
        raise HTTPException(status_code=400, detail="Analysis not completed")

    try:
        datalog_path = session["datalog"]["file_path"]
        tune_path = session["tune"]["file_path"]
        definition_path = session.get("definition", {}).get("file_path")

        results = rom_manager.analyze_rom_package(
            datalog_path, tune_path, definition_path
        )
        tables = results["detailed_data"]["rom_tables"]

        if category:
            category_keywords = {
                "fuel": ["fuel", "injector", "pulse"],
                "timing": ["timing", "ignition"],
                "boost": ["boost", "wastegate"],
                "idle": ["idle", "iac"],
                "learning": ["learning", "correction"],
            }
            if category.lower() in category_keywords:
                keywords = category_keywords[category.lower()]
                tables = [
                    t for t in tables if any(kw in t["name"].lower() for kw in keywords)
                ]

        return to_python_types(
            {
                "session_id": session_id,
                "total_tables": len(tables),
                "category_filter": category,
                "tables": tables,
            }
        )
    except Exception as e:
        logger.error(f"Failed to get ROM tables for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/{session_id}/export_changes")
async def export_tune_changes(
    session_id: str,
    format: str = Body("json", embed=True),
    user: dict = Depends(verify_token),
):
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if format not in ["json", "csv", "xml"]:
        raise HTTPException(status_code=400, detail="Unsupported export format")

    try:
        datalog_path = session["datalog"]["file_path"]
        tune_path = session["tune"]["file_path"]
        definition_path = session.get("definition", {}).get("file_path")

        results = rom_manager.analyze_rom_package(
            datalog_path, tune_path, definition_path
        )

        export_dir = f"./exports/{session_id}"
        os.makedirs(export_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"tune_changes_{timestamp}.{format}"
        filepath = f"{export_dir}/{filename}"

        if format == "json":
            with open(filepath, "w") as f:
                json.dump(results, f, indent=2, default=str)
        elif format == "csv":
            changes_data = []
            for change in results["detailed_data"]["tune_change_details"]:
                for cell_change in change.get("cell_changes", []):
                    changes_data.append(
                        {
                            "table_name": change["table_name"],
                            "row": cell_change["row"],
                            "col": cell_change["col"],
                            "rpm": cell_change["rpm"],
                            "load": cell_change["load"],
                            "old_value": cell_change["old_value"],
                            "new_value": cell_change["new_value"],
                            "change_percent": cell_change["change_percent"],
                            "priority": change["priority"],
                        }
                    )
            df = pd.DataFrame(changes_data)
            df.to_csv(filepath, index=False)
        else:
            # XML export not implemented yet
            raise HTTPException(status_code=501, detail="XML export not implemented")

        return {
            "status": "success",
            "export_file": filename,
            "format": format,
            "download_url": f"/api/download/{session_id}/{filename}",
        }
    except Exception as e:
        logger.error(f"Failed to export tune changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/status")
async def get_system_status(user: dict = Depends(verify_token)):
    return {
        "status": "operational",
        "version": "3.0.0",
        "features": {
            "xml_definition_parsing": True,
            "rom_table_extraction": True,
            "enhanced_tune_analysis": True,
            "legacy_compatibility": legacy_modules_available,
        },
        "statistics": {
            "active_sessions": len(active_sessions),
            "total_sessions": usage_stats["total_sessions"],
            "cache_size": (
                len(rom_manager.cache) if hasattr(rom_manager, "cache") else 0
            ),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/admin/clear_cache")
async def clear_system_cache(user: dict = Depends(is_admin)):
    try:
        rom_manager.clear_cache()
        return {
            "status": "success",
            "message": "System cache cleared",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
