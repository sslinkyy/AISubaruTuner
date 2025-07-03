
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SafetyConfig:
    afr_critical_threshold: float = 16.0
    afr_warning_threshold: float = 15.0
    timing_critical_degrees: float = 25.0
    boost_warning_psi: float = 20.0

def run_safety_checks(
    tune_data: Dict,
    datalog_data: Dict,
    config: Optional[SafetyConfig] = None,
) -> Dict[str, Any]:
    """Run comprehensive safety checks on tune and datalog data."""

    config = config or SafetyConfig()

    safety_results = {
        "overall_status": "safe",
        "critical_issues": [],
        "warnings": [],
        "recommendations": [],
        "safety_rating": "Safe",  # note: initialize rating
    }

    # Check for dangerous AFR values
    afr_check = check_afr_safety(datalog_data, config)
    if afr_check["critical"]:
        safety_results["critical_issues"].extend(afr_check["issues"])
        safety_results["overall_status"] = "unsafe"
    elif afr_check["warnings"]:
        safety_results["warnings"].extend(afr_check["warnings"])

    # Check ignition timing safety
    timing_check = check_timing_safety(tune_data, datalog_data, config)
    if timing_check["critical"]:
        safety_results["critical_issues"].extend(timing_check["issues"])
        safety_results["overall_status"] = "unsafe"

    # Check boost levels
    boost_check = check_boost_safety(datalog_data, config)
    if boost_check["warnings"]:
        safety_results["warnings"].extend(boost_check["warnings"])

    # Assign safety rating based on detected issues
    safety_results["safety_rating"] = _compute_safety_rating(
        len(safety_results["critical_issues"]), len(safety_results["warnings"])
    )

    return safety_results


def _compute_safety_rating(critical_count: int, warning_count: int) -> str:
    """Return a simple safety rating string."""
    if critical_count > 3 or warning_count > 10:
        return "Aggressive"
    if critical_count > 1 or warning_count > 5:
        return "Moderate"
    if critical_count > 0 or warning_count > 2:
        return "Conservative"
    return "Safe"

def check_afr_safety(datalog_data: Dict, config: SafetyConfig) -> Dict[str, Any]:
    """Check AFR values for safety."""
    result = {"critical": False, "warnings": [], "issues": []}

    data = datalog_data.get("data", [])
    if not data:
        return result

    # Check for dangerously lean conditions
    for i, row in enumerate(data):
        afr = row.get("A/F Sensor #1 (AFR)", 0)
        load = row.get("Engine Load", 0)

        if afr > config.afr_critical_threshold and load > 80:
            result["critical"] = True
            result["issues"].append({
                "type": "Critical AFR",
                "message": f"Dangerously lean AFR ({afr}) under high load at row {i}",
                "severity": "critical"
            })
        elif afr > config.afr_warning_threshold and load > 40:
            result["warnings"].append(
                f"Lean AFR {afr} detected at row {i}; consider enrichment"
            )

    return result

def check_timing_safety(
    tune_data: Dict, datalog_data: Dict, config: SafetyConfig
) -> Dict[str, Any]:
    """Check ignition timing safety."""
    result = {"critical": False, "warnings": [], "issues": []}

    data = datalog_data.get("data", [])
    if not data:
        return result

    # Check for excessive timing advance
    for i, row in enumerate(data):
        timing = row.get("Ignition Total Timing (degrees)", 0)
        knock = row.get("Knock", 0)

        if timing > config.timing_critical_degrees and knock > 0:
            result["critical"] = True
            result["issues"].append({
                "type": "Dangerous Timing",
                "message": f"Excessive timing ({timing}°) with knock detected at row {i}",
                "severity": "critical"
            })

    return result

def check_boost_safety(datalog_data: Dict, config: SafetyConfig) -> Dict[str, Any]:
    """Check boost pressure safety."""
    result = {"warnings": []}

    data = datalog_data.get("data", [])
    if not data:
        return result

    # Check for boost spikes
    boost_values = [row.get("Manifold Absolute Pressure (psi)", 0) for row in data]
    max_boost = max(boost_values) if boost_values else 0

    if max_boost > config.boost_warning_psi:
        result["warnings"].append({
            "type": "High Boost",
            "message": f"Maximum boost pressure: {max_boost} psi",
            "severity": "warning"
        })

    return result
