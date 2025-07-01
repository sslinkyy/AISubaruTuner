from typing import Dict, List, Any
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def generate_suggestions(analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate AI-powered tuning suggestions based on actual datalog analysis"""
    suggestions = []

    datalog = analysis_data.get("datalog", {})
    tune = analysis_data.get("tune", {})
    platform = analysis_data.get("platform", "")
    issues = analysis_data.get("issues", [])

    # Get the actual datalog data
    datalog_data = datalog.get("data", [])

    if not datalog_data:
        logger.warning("No datalog data available for analysis")
        return [{
            "id": "no_data",
            "type": "Data Issue",
            "priority": "low",
            "description": "No datalog data available for analysis",
            "parameter": "datalog",
            "change_type": "none",
            "affected_areas": "all",
            "safety_impact": "Cannot assess without data",
            "performance_impact": "Cannot assess without data"
        }]

    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(datalog_data)

    # Analyze A/F Corrections
    if "A/F Correction #1 (%)" in df.columns:
        af_corrections = df["A/F Correction #1 (%)"].dropna()
        high_corrections = af_corrections[af_corrections > 5].count()
        avg_correction = af_corrections.mean()

        if high_corrections > len(af_corrections) * 0.1:  # More than 10% of readings
            suggestions.append({
                "id": "fuel_correction_high",
                "type": "Fuel Map Adjustment",
                "priority": "high",
                "description": f"High A/F corrections detected (avg: {avg_correction:.1f}%). ECU is constantly correcting fuel delivery.",
                "parameter": "fuel_map",
                "change_type": "increase",
                "percentage": min(int(avg_correction), 10),
                "affected_areas": "Areas with high A/F corrections",
                "safety_impact": "Reduces ECU correction load, improves consistency",
                "performance_impact": "Better fuel delivery, more consistent power"
            })

    # Analyze AFR values
    if "A/F Sensor #1 (AFR)" in df.columns:
        afr_values = df["A/F Sensor #1 (AFR)"].dropna()
        lean_count = afr_values[afr_values > 15.0].count()
        avg_afr = afr_values.mean()

        if lean_count > 0:
            # Determine typical load (psia) and RPM for lean events
            psia = None
            rpm = None

            psia_range = None
            rpm_range = None
            if "Manifold Absolute Pressure (psi)" in df.columns:
                lean_psia = df.loc[afr_values > 15.0, "Manifold Absolute Pressure (psi)"].dropna()
                psia = lean_psia.mean()
                if not lean_psia.empty:
                    psia_range = [float(lean_psia.min()), float(lean_psia.max())]
            if "Engine Speed (rpm)" in df.columns:
                lean_rpm = df.loc[afr_values > 15.0, "Engine Speed (rpm)"].dropna()
                rpm = lean_rpm.mean()
                if not lean_rpm.empty:
                    rpm_range = [int(lean_rpm.min()), int(lean_rpm.max())]
            if "Manifold Absolute Pressure (psi)" in df.columns:
                psia = df.loc[afr_values > 15.0, "Manifold Absolute Pressure (psi)"].mean()
            if "Engine Speed (rpm)" in df.columns:
                rpm = df.loc[afr_values > 15.0, "Engine Speed (rpm)"].mean()

            suggestions.append({
                "id": "afr_lean_condition",
                "type": "Fuel Enrichment",
                "priority": "critical",
                "description": f"Detected {lean_count} lean AFR readings (>15.0). Average AFR: {avg_afr:.2f}",
                "parameter": "fuel_map",
                "change_type": "increase",
                "percentage": 8,
                "psia": round(float(psia), 1) if psia is not None else None,
                "rpm": int(round(float(rpm))) if rpm is not None else None,
                "tuning_cells": {
                    "psia_range": [round(psia_range[0], 1), round(psia_range[1], 1)] if psia_range else None,
                    "rpm_range": rpm_range,
                },
                "tuning_strategy": "weighted_average_4x4",
                "affected_areas": "Lean AFR regions",
                "safety_impact": "Critical - prevents engine damage from lean conditions",
                "performance_impact": "Safer operation, prevents detonation"
            })

    # Analyze boost pressure
    if "Manifold Absolute Pressure (psi)" in df.columns:
        boost_values = df["Manifold Absolute Pressure (psi)"].dropna()
        max_boost = boost_values.max()
        avg_boost = boost_values.mean()

        if max_boost < 8:  # Low boost for a turbo Subaru
            suggestions.append({
                "id": "boost_low",
                "type": "Boost Analysis",
                "priority": "medium",
                "description": f"Low boost pressure detected (max: {max_boost:.1f} psi). Check for boost leaks or conservative tune.",
                "parameter": "boost_control",
                "change_type": "investigate",
                "affected_areas": "Boost system",
                "safety_impact": "Neutral - diagnostic recommendation",
                "performance_impact": "Potential power gains if boost system optimized"
            })

    # Analyze ignition timing
    if "Ignition Total Timing (degrees)" in df.columns:
        timing_values = df["Ignition Total Timing (degrees)"].dropna()
        max_timing = timing_values.max()
        avg_timing = timing_values.mean()

        if max_timing < 20:  # Conservative timing
            suggestions.append({
                "id": "timing_conservative",
                "type": "Ignition Timing Optimization",
                "priority": "medium",
                "description": f"Conservative timing detected (max: {max_timing:.1f}°). Potential for optimization.",
                "parameter": "ignition_map",
                "change_type": "optimize",
                "degrees": 2,
                "affected_areas": "Low-medium load regions",
                "safety_impact": "Monitor for knock during changes",
                "performance_impact": "Potential power and efficiency gains"
            })

    # Analyze engine load vs timing relationship
    if "Engine Speed (rpm)" in df.columns and "Ignition Total Timing (degrees)" in df.columns:
        rpm_values = df["Engine Speed (rpm)"].dropna()
        idle_data = df[rpm_values < 1200]

        if len(idle_data) > len(df) * 0.8:  # Mostly idle data
            suggestions.append({
                "id": "idle_tune_focus",
                "type": "Idle Optimization",
                "priority": "low",
                "description": "Datalog contains mostly idle data. Consider logging during driving for better tune analysis.",
                "parameter": "idle_maps",
                "change_type": "optimize",
                "affected_areas": "Idle and low RPM regions",
                "safety_impact": "Low risk",
                "performance_impact": "Improved idle quality and fuel economy"
            })

    # Generate issue-based suggestions
    for issue in issues:
        if issue["type"] == "lean_condition":
            suggestions.append({
                "id": f"issue_based_{len(suggestions)}",
                "type": "Critical Fuel Adjustment",
                "priority": "critical",
                "description": f"Addressing detected issue: {issue.get('description', 'Lean condition detected')}",
                "parameter": "fuel_map",
                "change_type": "increase",
                "percentage": 10,
                "affected_areas": "High correction areas",
                "safety_impact": "Critical - prevents engine damage",
                "performance_impact": "Safer operation, consistent power delivery"
            })

    # Platform-specific suggestions
    if platform == "Subaru":
        suggestions.extend(generate_subaru_specific_suggestions(df))
    elif platform == "Hondata":
        suggestions.extend(generate_hondata_specific_suggestions(df))

    # If no specific suggestions generated, provide general guidance
    if not suggestions:
        suggestions.append({
            "id": "general_guidance",
            "type": "General Tuning Guidance",
            "priority": "low",
            "description": "Datalog appears normal. Continue monitoring and consider more aggressive driving scenarios for comprehensive analysis.",
            "parameter": "monitoring",
            "change_type": "continue",
            "affected_areas": "All systems",
            "safety_impact": "Maintain current safety margins",
            "performance_impact": "Baseline established for future optimization"
        })

    return suggestions

def generate_subaru_specific_suggestions(df: pd.DataFrame) -> List[Dict]:
    """Generate Subaru-specific suggestions based on datalog analysis"""
    suggestions = []

    # Check for AVCS-related parameters
    if "Engine Speed (rpm)" in df.columns:
        rpm_data = df["Engine Speed (rpm)"].dropna()
        mid_range_data = df[(rpm_data >= 2000) & (rpm_data <= 4000)]

        if len(mid_range_data) > 10:
            suggestions.append({
                "id": "subaru_avcs_optimization",
                "type": "AVCS Timing Optimization",
                "priority": "medium",
                "description": "Mid-range RPM data available for AVCS optimization analysis",
                "parameter": "avcs_map",
                "change_type": "optimize",
                "affected_areas": "2000-4000 RPM range",
                "safety_impact": "Low risk with proper monitoring",
                "performance_impact": "Improved mid-range torque and response"
            })

    # Check for knock sensor data
    knock_columns = [col for col in df.columns if 'knock' in col.lower()]
    if not knock_columns:
        suggestions.append({
            "id": "subaru_knock_monitoring",
            "type": "Safety Enhancement",
            "priority": "high",
            "description": "No knock sensor data detected. Add knock monitoring for safe tuning.",
            "parameter": "knock_sensor",
            "change_type": "add_logging",
            "affected_areas": "All load/RPM ranges",
            "safety_impact": "Critical for safe tuning",
            "performance_impact": "Enables more aggressive tuning with safety"
        })

    return suggestions

def generate_hondata_specific_suggestions(df: pd.DataFrame) -> List[Dict]:
    """Generate Hondata-specific suggestions"""
    suggestions = []

    # VTEC-related suggestions would go here
    if "Engine Speed (rpm)" in df.columns:
        rpm_data = df["Engine Speed (rpm)"].dropna()
        high_rpm_data = df[rpm_data > 5000]

        if len(high_rpm_data) > 0:
            suggestions.append({
                "id": "hondata_vtec_optimization",
                "type": "VTEC Optimization",
                "priority": "medium",
                "description": "High RPM data available for VTEC analysis",
                "parameter": "vtec_point",
                "change_type": "optimize",
                "affected_areas": "High RPM range",
                "safety_impact": "Monitor for over-rev conditions",
                "performance_impact": "Optimized high-RPM power delivery"
            })

    return suggestions
