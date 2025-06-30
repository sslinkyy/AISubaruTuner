
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def optimize_tune(tune_data: Dict, datalog_data: Dict, suggestions: List[Dict]) -> Dict[str, Any]:
    """Generate optimized tune based on datalog analysis and suggestions"""

    optimized_tune = {
        "base_tune": tune_data,
        "changes": [],
        "optimization_summary": {
            "total_changes": 0,
            "safety_improvements": 0,
            "performance_improvements": 0
        }
    }

    # Process each suggestion
    for suggestion in suggestions:
        change = generate_tune_change(suggestion, datalog_data)
        if change:
            optimized_tune["changes"].append(change)
            optimized_tune["optimization_summary"]["total_changes"] += 1

            if suggestion.get("priority") in ["critical", "high"]:
                optimized_tune["optimization_summary"]["safety_improvements"] += 1
            else:
                optimized_tune["optimization_summary"]["performance_improvements"] += 1

    return optimized_tune

def generate_tune_change(suggestion: Dict, datalog_data: Dict) -> Dict[str, Any]:
    """Generate specific tune change from suggestion"""

    change = {
        "id": suggestion["id"],
        "parameter": suggestion["parameter"],
        "type": suggestion["type"],
        "description": suggestion["description"],
        "priority": suggestion["priority"]
    }

    if suggestion["type"] == "Fuel Map Adjustment":
        change.update({
            "map_type": "fuel",
            "adjustment_type": suggestion["change_type"],
            "percentage": suggestion.get("percentage", 5),
            "affected_cells": calculate_affected_cells(datalog_data, "fuel")
        })

    elif suggestion["type"] == "Ignition Timing Adjustment":
        change.update({
            "map_type": "ignition",
            "adjustment_type": suggestion["change_type"],
            "degrees": suggestion.get("degrees", 2),
            "affected_cells": calculate_affected_cells(datalog_data, "timing")
        })

    return change

def calculate_affected_cells(datalog_data: Dict, map_type: str) -> List[Dict]:
    """Calculate which tune map cells should be affected"""
    affected_cells = []

    data = datalog_data.get("data", [])
    if not data:
        return affected_cells

    # Group data by RPM and load ranges
    rpm_ranges = [(1000, 2000), (2000, 3000), (3000, 4000), (4000, 5000), (5000, 7000)]
    load_ranges = [(0, 25), (25, 50), (50, 75), (75, 100)]

    for rpm_range in rpm_ranges:
        for load_range in load_ranges:
            # Find data points in this cell
            cell_data = [
                row for row in data
                if rpm_range[0] <= row.get("Engine Speed (rpm)", 0) < rpm_range[1]
                and load_range[0] <= row.get("Engine Load", 0) < load_range[1]
            ]

            if cell_data:
                affected_cells.append({
                    "rpm_range": rpm_range,
                    "load_range": load_range,
                    "data_points": len(cell_data),
                    "avg_values": calculate_cell_averages(cell_data)
                })

    return affected_cells

def calculate_cell_averages(cell_data: List[Dict]) -> Dict:
    """Calculate average values for a tune map cell"""
    if not cell_data:
        return {}

    averages = {}
    numeric_fields = ["A/F Sensor #1 (AFR)", "Ignition Total Timing (degrees)", "Knock"]

    for field in numeric_fields:
        values = [row.get(field, 0) for row in cell_data if row.get(field) is not None]
        if values:
            averages[field] = sum(values) / len(values)

    return averages
