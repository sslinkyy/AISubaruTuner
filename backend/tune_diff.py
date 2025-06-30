
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TuneDiffResult:
    parameter: str
    old_value: Any
    new_value: Any
    change_type: str
    impact: str

def compute_tune_diff(current: Dict, proposed: Dict) -> List[TuneDiffResult]:
    """Compute differences between current and proposed tune"""
    diffs = []

    # Compare all parameters
    all_keys = set(current.keys()) | set(proposed.keys())

    for key in all_keys:
        old_val = current.get(key)
        new_val = proposed.get(key)

        if old_val != new_val:
            change_type = determine_change_type(old_val, new_val)
            impact = assess_change_impact(key, old_val, new_val)

            diffs.append(TuneDiffResult(
                parameter=key,
                old_value=old_val,
                new_value=new_val,
                change_type=change_type,
                impact=impact
            ))

    return diffs

def determine_change_type(old_val: Any, new_val: Any) -> str:
    """Determine the type of change"""
    if old_val is None:
        return "added"
    elif new_val is None:
        return "removed"
    elif isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
        if new_val > old_val:
            return "increased"
        else:
            return "decreased"
    else:
        return "modified"

def assess_change_impact(parameter: str, old_val: Any, new_val: Any) -> str:
    """Assess the impact of a parameter change"""
    critical_params = ["fuel_map", "ignition_map", "boost_target"]

    if parameter in critical_params:
        return "high"
    else:
        return "medium"
