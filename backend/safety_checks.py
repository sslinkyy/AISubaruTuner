
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def run_safety_checks(tune_data: Dict, datalog_data: Dict) -> Dict[str, Any]:
    """Run comprehensive safety checks on tune and datalog data"""

    safety_results = {
        "overall_status": "safe",
        "critical_issues": [],
        "warnings": [],
        "recommendations": []
    }

    # Check for dangerous AFR values
    afr_check = check_afr_safety(datalog_data)
    if afr_check["critical"]:
        safety_results["critical_issues"].extend(afr_check["issues"])
        safety_results["overall_status"] = "unsafe"
    elif afr_check["warnings"]:
        safety_results["warnings"].extend(afr_check["warnings"])

    # Check ignition timing safety
    timing_check = check_timing_safety(tune_data, datalog_data)
    if timing_check["critical"]:
        safety_results["critical_issues"].extend(timing_check["issues"])
        safety_results["overall_status"] = "unsafe"

    # Check boost levels
    boost_check = check_boost_safety(datalog_data)
    if boost_check["warnings"]:
        safety_results["warnings"].extend(boost_check["warnings"])

    return safety_results

def check_afr_safety(datalog_data: Dict) -> Dict[str, Any]:
    """Check AFR values for safety"""
    result = {"critical": False, "warnings": [], "issues": []}

    data = datalog_data.get("data", [])
    if not data:
        return result

    # Check for dangerously lean conditions
    for i, row in enumerate(data):
        afr = row.get("A/F Sensor #1 (AFR)", 0)
        load = row.get("Engine Load", 0)

        if afr > 16 and load > 80:  # Very lean under high load
            result["critical"] = True
            result["issues"].append({
                "type": "Critical AFR",
                "message": f"Dangerously lean AFR ({afr}) under high load at row {i}",
                "severity": "critical"
            })

    return result

def check_timing_safety(tune_data: Dict, datalog_data: Dict) -> Dict[str, Any]:
    """Check ignition timing safety"""
    result = {"critical": False, "warnings": [], "issues": []}

    data = datalog_data.get("data", [])
    if not data:
        return result

    # Check for excessive timing advance
    for i, row in enumerate(data):
        timing = row.get("Ignition Total Timing (degrees)", 0)
        knock = row.get("Knock", 0)

        if timing > 25 and knock > 0:  # High timing with knock
            result["critical"] = True
            result["issues"].append({
                "type": "Dangerous Timing",
                "message": f"Excessive timing ({timing}°) with knock detected at row {i}",
                "severity": "critical"
            })

    return result

def check_boost_safety(datalog_data: Dict) -> Dict[str, Any]:
    """Check boost pressure safety"""
    result = {"warnings": []}

    data = datalog_data.get("data", [])
    if not data:
        return result

    # Check for boost spikes
    boost_values = [row.get("Manifold Absolute Pressure (psi)", 0) for row in data]
    max_boost = max(boost_values) if boost_values else 0

    if max_boost > 20:  # High boost warning
        result["warnings"].append({
            "type": "High Boost",
            "message": f"Maximum boost pressure: {max_boost} psi",
            "severity": "warning"
        })

    return result
