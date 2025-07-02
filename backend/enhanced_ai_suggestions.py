from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
import logging
import pandas as pd
import numpy as np
import math
import re

logger = logging.getLogger(__name__)

@dataclass
class AIConfig:
    """Configuration for :class:`EnhancedTuningAI`. Allows expert users to
    override default thresholds without modifying the code."""

    tuning_parameters: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            "fuel": {
                "safe_change_limit": 15.0,
                "critical_afr_lean": 15.5,
                "critical_afr_rich": 11.5,
                "target_afr_na": 14.7,
                "target_afr_boost": 12.5
            },
            "timing": {
                "safe_change_limit": 5.0,
                "conservative_advance": 2.0,
                "knock_retard": 3.0,
                "idle_timing": 15.0
            },
            "boost": {
                "safe_change_limit": 3.0,
                "max_safe_boost": 20.0,
                "wastegate_duty_max": 85.0
            }
        }
    )

    trend_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "min_interval_points": 5,
            "lean_delta": 0.3,
            "lean_afr_threshold": 14.7,
            "load_rise_delta": 3.0,
        }
    )


class EnhancedTuningAI:
    """Enhanced AI tuning suggestions with comprehensive analysis."""

    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        self.tuning_parameters = self.config.tuning_parameters
        self.trend_thresholds = self.config.trend_thresholds

    def _validate_analysis_data(self, analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Simple validation for incoming analysis data."""
        if not isinstance(analysis_data, dict):
            return False, "Analysis data must be a dictionary"

        datalog = analysis_data.get("datalog")
        if not datalog or not isinstance(datalog.get("data", []), list):
            return False, "Datalog information missing or malformed"

        return True, ""

    def generate_comprehensive_suggestions(
        self,
        analysis_data: Dict[str, Any],
        interval_size: int = 1000,
        load_interval_size: int = 5,
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive tuning suggestions with specific RPM/load context
        and aggregate them by RPM interval.

        ``interval_size`` specifies the step for grouping suggestions. It can be
        either ``500`` or ``1000`` RPM. Any value outside of these choices will
        default to ``1000`` RPM."""

        valid, message = self._validate_analysis_data(analysis_data)
        if not valid:
            logger.warning("Invalid analysis data provided: %s", message)
            return [
                {
                    "id": "invalid_input",
                    "type": "Input Error",
                    "priority": "high",
                    "description": message,
                    "specific_action": "Verify datalog and tune information",
                }
            ]

        suggestions = []
        datalog = analysis_data.get("datalog", {})
        platform = analysis_data.get("platform", "")
        issues = analysis_data.get("issues", [])

        # normalize interval size
        if interval_size not in (500, 1000):
            interval_size = 1000
        if load_interval_size <= 0:
            load_interval_size = 5

        # Get the actual datalog data
        datalog_data = datalog.get("data", [])

        if not datalog_data:
            return self._generate_no_data_suggestions()

        # Convert to DataFrame for analysis
        df = pd.DataFrame(datalog_data)
        logger.info(f"Analyzing {len(df)} datalog records with {len(df.columns)} parameters")

        # Generate fuel-related suggestions
        suggestions.extend(self._analyze_fuel_system(df, issues))

        # Generate timing suggestions
        suggestions.extend(self._analyze_ignition_timing(df, issues))

        # Generate boost control suggestions
        suggestions.extend(self._analyze_boost_system(df, issues))

        # Generate load-specific suggestions
        suggestions.extend(self._analyze_load_specific_areas(df, issues))

        # Warmup, tip-in and compensation analysis
        suggestions.extend(self._analyze_enrichments_and_compensations(df))

        # Generate safety and monitoring suggestions
        suggestions.extend(self._analyze_safety_monitoring(df, issues))

        # Platform-specific advanced suggestions
        if platform == "Subaru":
            suggestions.extend(self._generate_subaru_advanced_suggestions(df))
        elif platform == "Hondata":
            suggestions.extend(self._generate_hondata_advanced_suggestions(df))

        # Trend-based analysis across RPM intervals
        suggestions.extend(self._analyze_trend_patterns(df, interval_size))

        # Sort by priority and return
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        suggestions.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2), reverse=True)

        # Break suggestions into RPM intervals for clarity
        grouped = self._group_suggestions_by_intervals(
            suggestions, interval_size, load_interval_size, df
        )

        return grouped[:20]

    def _analyze_fuel_system(self, df: pd.DataFrame, issues: List[Dict]) -> List[Dict[str, Any]]:
        """Comprehensive fuel system analysis with specific recommendations"""
        suggestions = []

        # A/F Correction Analysis
        if "A/F Correction #1 (%)" in df.columns:
            af_corrections = df["A/F Correction #1 (%)"].dropna()

            # Analyze corrections by RPM/load
            rpm_load_corrections = self._analyze_corrections_by_load_points(df, af_corrections)

            for area in rpm_load_corrections:
                if abs(area["avg_correction"]) > 8:
                    suggestions.append({
                        "id": f"fuel_correction_{area['rpm_range']}_{area['load_range']}",
                        "type": "Fuel Map Correction",
                        "priority": "high" if abs(area["avg_correction"]) > 15 else "medium",
                        "table": "Primary_Open_Loop_Fueling",
                        "description": f"At {area['rpm_range']} RPM and {area['load_range']} load: ECU applying {area['avg_correction']:+.1f}% fuel correction",
                        "specific_action": f"Adjust fuel map by {area['recommended_change']:+.1f}% in this area",
                        "rpm_range": area["rpm_range"],
                        "load_range": area["load_range"],
                        "current_correction": f"{area['avg_correction']:+.1f}%",
                        "recommended_change": f"{area['recommended_change']:+.1f}%",
                        "data_points": area["data_points"],
                        "confidence": "high" if area["data_points"] > 20 else "medium",
                        "parameter": "fuel_map",
                        "change_type": "increase" if area["avg_correction"] > 0 else "decrease",
                        "percentage": abs(area["recommended_change"]),
                        "affected_areas": f"{area['rpm_range']} RPM, {area['load_range']} load",
                        "safety_impact": "Reduces ECU correction load, improves fuel delivery consistency",
                        "performance_impact": f"Eliminates {abs(area['avg_correction']):.1f}% fuel correction, smoother power delivery",
                        "validation_method": "Monitor A/F corrections after change - should reduce to <5%"
                    })

        # AFR Analysis with specific recommendations
        if "A/F Sensor #1 (AFR)" in df.columns:
            afr_analysis = self._analyze_afr_by_conditions(df)

            for condition in afr_analysis:
                if condition["issue_detected"]:
                    suggestions.append({
                        "id": f"afr_correction_{condition['condition']}",
                        "type": "AFR Optimization",
                        "priority": condition["priority"],
                        "table": "Primary_Open_Loop_Fueling",
                        "description": f"AFR issue in {condition['condition']}: {condition['description']}",
                        "specific_action": condition["recommendation"],
                        "rpm_range": condition["rpm_range"],
                        "load_range": condition["load_range"],
                        "current_afr": f"{condition['avg_afr']:.2f}",
                        "target_afr": f"{condition['target_afr']:.2f}",
                        "fuel_change_needed": f"{condition['fuel_change']:+.1f}%",
                        "data_points": condition["data_points"],
                        "confidence": condition["confidence"],
                        "parameter": "fuel_map",
                        "change_type": "increase" if condition["fuel_change"] > 0 else "decrease",
                        "percentage": abs(condition["fuel_change"]),
                        "affected_areas": f"{condition['rpm_range']} RPM, {condition['load_range']} load",
                        "safety_impact": condition["safety_impact"],
                        "performance_impact": condition["performance_impact"],
                        "validation_method": f"Target AFR should be {condition['target_afr']:.1f} ± 0.3"
                    })

        # Injector duty cycle analysis
        if "Injector Duty Cycle (%)" in df.columns:
            duty_analysis = self._analyze_injector_duty(df)
            if duty_analysis["max_duty"] > 85:
                suggestions.append({
                    "id": "injector_duty_high",
                    "type": "Injector Capacity Warning",
                    "priority": "high",
                    "table": "Injector_Scaling",
                    "description": f"High injector duty cycle detected: {duty_analysis['max_duty']:.1f}% at {duty_analysis['max_duty_rpm']} RPM",
                    "specific_action": f"Consider larger injectors or reduce fuel demand in high-load areas",
                    "rpm_range": f"{duty_analysis['max_duty_rpm']-200}-{duty_analysis['max_duty_rpm']+200}",
                    "load_range": "High load",
                    "current_duty": f"{duty_analysis['max_duty']:.1f}%",
                    "safe_limit": "85%",
                    "data_points": duty_analysis["high_duty_points"],
                    "confidence": "high",
                    "parameter": "injector_sizing",
                    "change_type": "hardware_upgrade",
                    "affected_areas": "High load/RPM areas",
                    "safety_impact": "Critical - prevents injector saturation and lean conditions",
                    "performance_impact": "Maintains proper fuel delivery at high power levels",
                    "validation_method": "Duty cycle should remain below 85% under all conditions"
                })

        return suggestions

    def _analyze_ignition_timing(self, df: pd.DataFrame, issues: List[Dict]) -> List[Dict[str, Any]]:
        """Comprehensive ignition timing analysis"""
        suggestions = []

        # Knock analysis with specific recommendations
        if "Knock Sum" in df.columns:
            knock_analysis = self._analyze_knock_by_conditions(df)

            for condition in knock_analysis:
                if condition["knock_detected"]:
                    suggestions.append({
                        "id": f"timing_knock_{condition['condition']}",
                        "type": "Knock Mitigation",
                        "priority": "critical",
                        "table": "Base_Ignition_Timing",
                        "description": f"Knock detected in {condition['condition']}: {condition['knock_events']} events",
                        "specific_action": f"Retard timing by {condition['recommended_retard']:.1f}° in this area",
                        "rpm_range": condition["rpm_range"],
                        "load_range": condition["load_range"],
                        "knock_events": condition["knock_events"],
                        "current_timing": f"{condition['avg_timing']:.1f}°",
                        "recommended_timing": f"{condition['avg_timing'] - condition['recommended_retard']:.1f}°",
                        "timing_change": f"-{condition['recommended_retard']:.1f}°",
                        "data_points": condition["data_points"],
                        "confidence": "high",
                        "parameter": "ignition_timing",
                        "change_type": "decrease",
                        "degrees": condition["recommended_retard"],
                        "affected_areas": f"{condition['rpm_range']} RPM, {condition['load_range']} load",
                        "safety_impact": "Critical - prevents engine damage from detonation",
                        "performance_impact": f"Slight power loss but safe operation in {condition['condition']}",
                        "validation_method": "Monitor knock sensors - should show zero knock events"
                    })

        # Timing optimization opportunities
        if "Ignition Total Timing (degrees)" in df.columns and "Knock Sum" in df.columns:
            timing_opportunities = self._find_timing_optimization_opportunities(df)

            for opportunity in timing_opportunities:
                suggestions.append({
                    "id": f"timing_optimize_{opportunity['area']}",
                    "type": "Timing Optimization",
                    "priority": "medium",
                    "table": "Base_Ignition_Timing",
                    "description": f"Timing optimization opportunity in {opportunity['area']}",
                    "specific_action": f"Advance timing by {opportunity['safe_advance']:.1f}° in this area",
                    "rpm_range": opportunity["rpm_range"],
                    "load_range": opportunity["load_range"],
                    "current_timing": f"{opportunity['current_timing']:.1f}°",
                    "recommended_timing": f"{opportunity['current_timing'] + opportunity['safe_advance']:.1f}°",
                    "timing_change": f"+{opportunity['safe_advance']:.1f}°",
                    "potential_gain": opportunity["estimated_gain"],
                    "data_points": opportunity["data_points"],
                    "confidence": opportunity["confidence"],
                    "parameter": "ignition_timing",
                    "change_type": "increase",
                    "degrees": opportunity["safe_advance"],
                    "affected_areas": f"{opportunity['rpm_range']} RPM, {opportunity['load_range']} load",
                    "safety_impact": "Monitor for knock - advance conservatively",
                    "performance_impact": f"Estimated {opportunity['estimated_gain']} improvement in {opportunity['area']}",
                    "validation_method": "Advance in 1° increments, monitor knock sensors"
                })

        return suggestions

    def _analyze_boost_system(self, df: pd.DataFrame, issues: List[Dict]) -> List[Dict[str, Any]]:
        """Comprehensive boost system analysis"""
        suggestions = []

        if "Manifold Absolute Pressure (psi)" in df.columns:
            boost_analysis = self._analyze_boost_control(df)

            # Boost target vs actual analysis
            if "Boost Target (psi)" in df.columns:
                boost_error_analysis = self._analyze_boost_error(df)

                for area in boost_error_analysis:
                    if abs(area["avg_error"]) > 1.5:
                        suggestions.append({
                            "id": f"boost_control_{area['rpm_range']}",
                            "type": "Boost Control Tuning",
                            "priority": "medium",
                            "table": "Wastegate_Duty_Cycle",
                            "description": f"Boost error in {area['rpm_range']} RPM: {area['avg_error']:+.1f} psi from target",
                            "specific_action": f"Adjust wastegate duty by {area['duty_adjustment']:+.1f}% in this RPM range",
                            "rpm_range": area["rpm_range"],
                            "load_range": "Boost conditions",
                            "current_error": f"{area['avg_error']:+.1f} psi",
                            "target_boost": f"{area['target_boost']:.1f} psi",
                            "actual_boost": f"{area['actual_boost']:.1f} psi",
                            "duty_adjustment": f"{area['duty_adjustment']:+.1f}%",
                            "data_points": area["data_points"],
                            "confidence": "high" if area["data_points"] > 15 else "medium",
                            "parameter": "boost_control",
                            "change_type": "increase" if area["avg_error"] < 0 else "decrease",
                            "percentage": abs(area["duty_adjustment"]),
                            "affected_areas": f"{area['rpm_range']} RPM boost control",
                            "safety_impact": "Improves boost accuracy and consistency",
                            "performance_impact": f"Eliminates {abs(area['avg_error']):.1f} psi boost error",
                            "validation_method": "Boost should track target within ±1 psi"
                        })

            # Boost spike detection
            boost_spikes = self._detect_boost_spikes(df)
            if boost_spikes["spikes_detected"]:
                suggestions.append({
                    "id": "boost_spike_control",
                    "type": "Boost Spike Control",
                    "priority": "high",
                    "table": "Boost_Control_PID",
                    "description": f"Boost spikes detected: {boost_spikes['max_spike']:.1f} psi spike",
                    "specific_action": f"Adjust boost control PID settings to reduce overshoot",
                    "rpm_range": boost_spikes["spike_rpm_range"],
                    "load_range": "Boost transition",
                    "max_spike": f"{boost_spikes['max_spike']:.1f} psi",
                    "spike_frequency": f"{boost_spikes['spike_count']} events",
                    "recommended_action": "Reduce I-gain by 20%, increase D-gain by 10%",
                    "data_points": boost_spikes["total_points"],
                    "confidence": "high",
                    "parameter": "boost_pid",
                    "change_type": "pid_tuning",
                    "affected_areas": "Boost transition areas",
                    "safety_impact": "Prevents boost spikes that can cause knock",
                    "performance_impact": "Smoother boost delivery and power curve",
                    "validation_method": "Boost should rise smoothly without overshoot >1 psi"
                })

        return suggestions

    def _analyze_load_specific_areas(self, df: pd.DataFrame, issues: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze specific load areas for targeted tuning"""
        suggestions = []

        # Idle analysis
        idle_analysis = self._analyze_idle_conditions(df)
        if idle_analysis["issues_found"]:
            suggestions.append({
                "id": "idle_optimization",
                "type": "Idle Quality Optimization",
                "priority": "low",
                "table": "Idle_Speed_Control",
                "description": f"Idle instability detected: {idle_analysis['description']}",
                "specific_action": idle_analysis["recommendation"],
                "rpm_range": "600-1000",
                "load_range": "Idle/vacuum",
                "idle_rpm_variation": f"±{idle_analysis['rpm_variation']:.0f} RPM",
                "target_idle": f"{idle_analysis['target_idle']} RPM",
                "data_points": idle_analysis["data_points"],
                "confidence": "medium",
                "parameter": "idle_control",
                "change_type": "optimize",
                "affected_areas": "Idle conditions",
                "safety_impact": "Improves idle stability and drivability",
                "performance_impact": "Smoother idle, better fuel economy",
                "validation_method": "Idle should be stable within ±50 RPM"
            })

        # Part throttle analysis
        part_throttle_analysis = self._analyze_part_throttle(df)
        for area in part_throttle_analysis:
            if area["optimization_needed"]:
                suggestions.append({
                    "id": f"part_throttle_{area['load_range']}",
                    "type": "Part Throttle Optimization",
                    "priority": "medium",
                    "table": "Primary_Open_Loop_Fueling",
                    "description": f"Part throttle optimization in {area['load_range']} load range",
                    "specific_action": area["recommendation"],
                    "rpm_range": area["rpm_range"],
                    "load_range": area["load_range"],
                    "current_afr": f"{area['avg_afr']:.2f}",
                    "target_afr": f"{area['target_afr']:.2f}",
                    "fuel_adjustment": f"{area['fuel_adjustment']:+.1f}%",
                    "data_points": area["data_points"],
                    "confidence": area["confidence"],
                    "parameter": "fuel_map",
                    "change_type": "optimize",
                    "percentage": abs(area["fuel_adjustment"]),
                    "affected_areas": f"{area['rpm_range']} RPM, {area['load_range']} load",
                    "safety_impact": "Optimizes part throttle drivability",
                    "performance_impact": "Improved throttle response and fuel economy",
                    "validation_method": f"AFR should target {area['target_afr']:.1f} in this range"
                })

        return suggestions

    def _analyze_safety_monitoring(self, df: pd.DataFrame, issues: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze safety monitoring and suggest improvements"""
        suggestions = []

        # Check for missing critical parameters
        critical_params = {
            "Knock Sum": "Knock monitoring",
            "A/F Sensor #1 (AFR)": "Air-fuel ratio monitoring",
            "Coolant Temperature (F)": "Engine temperature monitoring",
            "Oil Temperature (F)": "Oil temperature monitoring"
        }

        missing_params = []
        for param, description in critical_params.items():
            if param not in df.columns:
                missing_params.append({"param": param, "description": description})

        if missing_params:
            suggestions.append({
                "id": "safety_monitoring_enhancement",
                "type": "Safety Monitoring Enhancement",
                "priority": "high",
                "table": "Datalog_Configuration",
                "description": f"Missing critical safety parameters in datalog",
                "specific_action": "Add missing parameters to datalog for comprehensive monitoring",
                "missing_parameters": [p["description"] for p in missing_params],
                "safety_impact": "Critical - enables detection of dangerous conditions",
                "performance_impact": "Enables safer, more aggressive tuning",
                "validation_method": "Verify all parameters are logging correctly",
                "parameter": "monitoring",
                "change_type": "add_logging",
                "affected_areas": "All operating conditions",
                "confidence": "high"
            })

        # Temperature analysis
        if "Coolant Temperature (F)" in df.columns:
            temp_analysis = self._analyze_temperatures(df)
            if temp_analysis["high_temps_detected"]:
                suggestions.append({
                    "id": "temperature_management",
                    "type": "Temperature Management",
                    "priority": "medium",
                    "table": "Fan_Control",
                    "description": f"High temperatures detected: {temp_analysis['max_temp']:.1f}°F",
                    "specific_action": temp_analysis["recommendation"],
                    "max_temperature": f"{temp_analysis['max_temp']:.1f}°F",
                    "safe_limit": "220°F",
                    "high_temp_duration": f"{temp_analysis['high_temp_duration']:.1f}s",
                    "data_points": temp_analysis["data_points"],
                    "confidence": "high",
                    "parameter": "cooling_system",
                    "change_type": "optimize",
                    "affected_areas": "High load conditions",
                    "safety_impact": "Prevents overheating and engine damage",
                    "performance_impact": "Maintains consistent power under load",
                    "validation_method": "Coolant temp should stay below 220°F"
                })

        return suggestions

    def _generate_subaru_advanced_suggestions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate Subaru-specific advanced suggestions"""
        suggestions = []

        # AVCS analysis
        if "AVCS Intake Position (degrees)" in df.columns:
            avcs_analysis = self._analyze_avcs_performance(df)
            if avcs_analysis["optimization_available"]:
                suggestions.append({
                    "id": "avcs_optimization",
                    "type": "AVCS Timing Optimization",
                    "priority": "medium",
                    "table": "AVCS_Map",
                    "description": f"AVCS optimization opportunity in {avcs_analysis['rpm_range']} RPM",
                    "specific_action": f"Adjust AVCS timing by {avcs_analysis['recommended_adjustment']:+.1f}° in mid-range",
                    "rpm_range": avcs_analysis["rpm_range"],
                    "load_range": avcs_analysis["load_range"],
                    "current_avcs": f"{avcs_analysis['avg_position']:.1f}°",
                    "recommended_avcs": f"{avcs_analysis['recommended_position']:.1f}°",
                    "estimated_gain": avcs_analysis["estimated_gain"],
                    "data_points": avcs_analysis["data_points"],
                    "confidence": "medium",
                    "parameter": "avcs_timing",
                    "change_type": "optimize",
                    "degrees": abs(avcs_analysis["recommended_adjustment"]),
                    "affected_areas": f"{avcs_analysis['rpm_range']} RPM mid-range",
                    "safety_impact": "Low risk - AVCS changes are generally safe",
                    "performance_impact": f"Estimated {avcs_analysis['estimated_gain']} torque improvement",
                    "validation_method": "Monitor torque curve and throttle response"
                })

        # Subaru-specific fuel trim analysis
        if "A/F Learning #1 (%)" in df.columns:
            learning_analysis = self._analyze_fuel_learning(df)
            if learning_analysis["excessive_learning"]:
                suggestions.append({
                    "id": "fuel_learning_correction",
                    "type": "Fuel Learning Correction",
                    "priority": "medium",
                    "table": "A/F_Learning_Limits",
                    "description": f"Excessive fuel learning detected: {learning_analysis['max_learning']:+.1f}%",
                    "specific_action": "Adjust base fuel maps to reduce learning corrections",
                    "max_learning": f"{learning_analysis['max_learning']:+.1f}%",
                    "avg_learning": f"{learning_analysis['avg_learning']:+.1f}%",
                    "affected_cells": learning_analysis["affected_areas"],
                    "data_points": learning_analysis["data_points"],
                    "confidence": "high",
                    "parameter": "fuel_learning",
                    "change_type": "base_map_adjustment",
                    "percentage": abs(learning_analysis["avg_learning"]) * 0.8,
                    "affected_areas": "Areas with high learning values",
                    "safety_impact": "Reduces ECU learning dependency",
                    "performance_impact": "More consistent fuel delivery",
                    "validation_method": "Learning values should reduce to <±8%"
                })

        return suggestions

    def _generate_hondata_advanced_suggestions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate Hondata-specific advanced suggestions"""
        suggestions = []

        # VTEC analysis
        if "Engine Speed (rpm)" in df.columns:
            vtec_analysis = self._analyze_vtec_transition(df)
            if vtec_analysis["optimization_needed"]:
                suggestions.append({
                    "id": "vtec_optimization",
                    "type": "VTEC Transition Optimization",
                    "priority": "medium",
                    "table": "VTEC_Engagement",
                    "description": f"VTEC transition optimization at {vtec_analysis['transition_rpm']} RPM",
                    "specific_action": vtec_analysis["recommendation"],
                    "transition_rpm": vtec_analysis["transition_rpm"],
                    "current_behavior": vtec_analysis["current_behavior"],
                    "recommended_change": vtec_analysis["recommended_change"],
                    "data_points": vtec_analysis["data_points"],
                    "confidence": "medium",
                    "parameter": "vtec_control",
                    "change_type": "optimize",
                    "affected_areas": f"VTEC transition around {vtec_analysis['transition_rpm']} RPM",
                    "safety_impact": "Monitor for over-rev conditions",
                    "performance_impact": "Smoother VTEC transition and power delivery",
                    "validation_method": "Check power curve smoothness through VTEC transition"
                })

        return suggestions

    # Helper methods for detailed analysis
    def _analyze_corrections_by_load_points(self, df: pd.DataFrame, corrections: pd.Series) -> List[Dict]:
        """Analyze A/F corrections by specific RPM/load points"""
        results = []

        if "Engine Speed (rpm)" not in df.columns or "Manifold Absolute Pressure (psi)" not in df.columns:
            return results

        # Define RPM and load bins
        rpm_bins = [(1500, 2500), (2500, 3500), (3500, 4500), (4500, 5500), (5500, 7000)]
        load_bins = [(-5, 0), (0, 5), (5, 10), (10, 15), (15, 25)]

        for rpm_range in rpm_bins:
            for load_range in load_bins:
                # Filter data for this RPM/load range
                rpm_mask = (df["Engine Speed (rpm)"] >= rpm_range[0]) & (df["Engine Speed (rpm)"] < rpm_range[1])
                load_data = df["Manifold Absolute Pressure (psi)"] - 14.7
                load_mask = (load_data >= load_range[0]) & (load_data < load_range[1])

                combined_mask = rpm_mask & load_mask
                area_corrections = corrections[combined_mask]

                if len(area_corrections) > 5:  # Need sufficient data
                    avg_correction = area_corrections.mean()

                    results.append({
                        "rpm_range": f"{rpm_range[0]}-{rpm_range[1]}",
                        "load_range": f"{load_range[0]:+.1f} to {load_range[1]:+.1f} psi",
                        "avg_correction": avg_correction,
                        "recommended_change": avg_correction * 0.8,  # Apply 80% of correction to base map
                        "data_points": len(area_corrections)
                    })

        return results

    def _analyze_afr_by_conditions(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze AFR by different operating conditions"""
        results = []

        if "A/F Sensor #1 (AFR)" not in df.columns:
            return results

        afr_data = df["A/F Sensor #1 (AFR)"].dropna()

        # Analyze different conditions
        conditions = [
            {"name": "idle", "rpm_range": (600, 1200), "load_range": (-5, 0), "target_afr": 14.7},
            {"name": "cruise", "rpm_range": (2000, 3500), "load_range": (0, 5), "target_afr": 14.7},
            {"name": "light_load", "rpm_range": (2000, 5000), "load_range": (5, 10), "target_afr": 13.5},
            {"name": "boost", "rpm_range": (3000, 6500), "load_range": (10, 25), "target_afr": 12.5}
        ]

        for condition in conditions:
            # Filter data for this condition
            if "Engine Speed (rpm)" in df.columns and "Manifold Absolute Pressure (psi)" in df.columns:
                rpm_mask = (df["Engine Speed (rpm)"] >= condition["rpm_range"][0]) & (df["Engine Speed (rpm)"] <= condition["rpm_range"][1])
                load_data = df["Manifold Absolute Pressure (psi)"] - 14.7
                load_mask = (load_data >= condition["load_range"][0]) & (load_data <= condition["load_range"][1])

                combined_mask = rpm_mask & load_mask
                condition_afr = afr_data[combined_mask]

                if len(condition_afr) > 10:
                    avg_afr = condition_afr.mean()
                    target_afr = condition["target_afr"]
                    afr_error = avg_afr - target_afr

                    # Calculate fuel change needed (approximate)
                    fuel_change = (afr_error / target_afr) * 100 * -1  # Negative because rich needs less fuel

                    issue_detected = abs(afr_error) > 0.5
                    priority = "critical" if abs(afr_error) > 1.5 else "high" if abs(afr_error) > 1.0 else "medium"

                    results.append({
                        "condition": condition["name"],
                        "rpm_range": f"{condition['rpm_range'][0]}-{condition['rpm_range'][1]}",
                        "load_range": f"{condition['load_range'][0]:+.1f} to {condition['load_range'][1]:+.1f} psi",
                        "avg_afr": avg_afr,
                        "target_afr": target_afr,
                        "afr_error": afr_error,
                        "fuel_change": fuel_change,
                        "data_points": len(condition_afr),
                        "issue_detected": issue_detected,
                        "priority": priority,
                        "confidence": "high" if len(condition_afr) > 20 else "medium",
                        "description": f"AFR {avg_afr:.2f} vs target {target_afr:.2f} ({afr_error:+.2f})",
                        "recommendation": f"Adjust fuel by {fuel_change:+.1f}% in {condition['name']} conditions",
                        "safety_impact": "Critical - maintains proper AFR for engine safety" if abs(afr_error) > 1.0 else "Optimizes AFR for performance",
                        "performance_impact": f"Corrects {abs(afr_error):.2f} AFR error in {condition['name']} conditions"
                    })

        return results

    def _analyze_injector_duty(self, df: pd.DataFrame) -> Dict:
        """Analyze injector duty cycle"""
        duty_data = df["Injector Duty Cycle (%)"].dropna()
        max_duty = duty_data.max()
        max_duty_idx = duty_data.idxmax()

        result = {
            "max_duty": max_duty,
            "avg_duty": duty_data.mean(),
            "high_duty_points": len(duty_data[duty_data > 80])
        }

        if "Engine Speed (rpm)" in df.columns:
            result["max_duty_rpm"] = df.loc[max_duty_idx, "Engine Speed (rpm)"]
        else:
            result["max_duty_rpm"] = 0

        return result

    def _analyze_knock_by_conditions(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze knock by operating conditions"""
        results = []

        if "Knock Sum" not in df.columns:
            return results

        knock_data = df["Knock Sum"].dropna()
        knock_events = df[knock_data > 0]

        if len(knock_events) == 0:
            return results

        # Analyze knock by RPM ranges
        rpm_ranges = [(2000, 3000), (3000, 4000), (4000, 5000), (5000, 6000), (6000, 8000)]

        for rpm_range in rpm_ranges:
            if "Engine Speed (rpm)" in df.columns:
                rpm_mask = (knock_events["Engine Speed (rpm)"] >= rpm_range[0]) & (knock_events["Engine Speed (rpm)"] < rpm_range[1])
                range_knock = knock_events[rpm_mask]

                if len(range_knock) > 0:
                    knock_count = len(range_knock)
                    avg_timing = range_knock["Ignition Total Timing (degrees)"].mean() if "Ignition Total Timing (degrees)" in range_knock.columns else 0

                    # Calculate recommended retard based on knock severity
                    recommended_retard = min(3.0, max(1.0, knock_count * 0.5))

                    results.append({
                        "condition": f"{rpm_range[0]}-{rpm_range[1]} RPM",
                        "rpm_range": f"{rpm_range[0]}-{rpm_range[1]}",
                        "load_range": "Various",
                        "knock_detected": True,
                        "knock_events": knock_count,
                        "avg_timing": avg_timing,
                        "recommended_retard": recommended_retard,
                        "data_points": len(range_knock)
                    })

        return results

    def _find_timing_optimization_opportunities(self, df: pd.DataFrame) -> List[Dict]:
        """Find safe timing advance opportunities"""
        opportunities = []

        if "Ignition Total Timing (degrees)" not in df.columns or "Knock Sum" not in df.columns:
            return opportunities

        # Find areas with no knock and conservative timing
        no_knock_data = df[df["Knock Sum"] == 0]

        if len(no_knock_data) < 50:
            return opportunities

        # Analyze by RPM ranges
        rpm_ranges = [(2000, 3000), (3000, 4000), (4000, 5000)]

        for rpm_range in rpm_ranges:
            if "Engine Speed (rpm)" in df.columns:
                rpm_mask = (no_knock_data["Engine Speed (rpm)"] >= rpm_range[0]) & (no_knock_data["Engine Speed (rpm)"] < rpm_range[1])
                range_data = no_knock_data[rpm_mask]

                if len(range_data) > 20:
                    avg_timing = range_data["Ignition Total Timing (degrees)"].mean()

                    # Conservative timing thresholds by RPM
                    conservative_thresholds = {
                        (2000, 3000): 25,
                        (3000, 4000): 22,
                        (4000, 5000): 20
                    }

                    threshold = conservative_thresholds.get(rpm_range, 20)

                    if avg_timing < threshold:
                        safe_advance = min(2.0, (threshold - avg_timing) * 0.5)

                        opportunities.append({
                            "area": f"{rpm_range[0]}-{rpm_range[1]} RPM",
                            "rpm_range": f"{rpm_range[0]}-{rpm_range[1]}",
                            "load_range": "No knock conditions",
                            "current_timing": avg_timing,
                            "safe_advance": safe_advance,
                            "estimated_gain": f"+{safe_advance * 2:.1f}% torque",
                            "data_points": len(range_data),
                            "confidence": "high" if len(range_data) > 50 else "medium"
                        })

        return opportunities

    def _analyze_boost_control(self, df: pd.DataFrame) -> Dict:
        """Analyze boost control system"""
        boost_data = df["Manifold Absolute Pressure (psi)"] - 14.7

        return {
            "max_boost": boost_data.max(),
            "avg_boost": boost_data.mean(),
            "boost_range": boost_data.max() - boost_data.min(),
            "high_boost_points": len(boost_data[boost_data > 15])
        }

    def _analyze_boost_error(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze boost target vs actual"""
        results = []

        if "Boost Target (psi)" not in df.columns:
            return results

        target_boost = df["Boost Target (psi)"].dropna()
        actual_boost = df["Manifold Absolute Pressure (psi)"] - 14.7
        boost_error = actual_boost - target_boost

        # Analyze by RPM ranges
        rpm_ranges = [(2000, 3000), (3000, 4000), (4000, 5000), (5000, 6500)]

        for rpm_range in rpm_ranges:
            if "Engine Speed (rpm)" in df.columns:
                rpm_mask = (df["Engine Speed (rpm)"] >= rpm_range[0]) & (df["Engine Speed (rpm)"] < rpm_range[1])
                range_error = boost_error[rpm_mask]
                range_target = target_boost[rpm_mask]
                range_actual = actual_boost[rpm_mask]

                if len(range_error) > 10:
                    avg_error = range_error.mean()

                    # Calculate duty cycle adjustment needed
                    duty_adjustment = avg_error * 5  # Rough approximation

                    results.append({
                        "rpm_range": f"{rpm_range[0]}-{rpm_range[1]}",
                        "avg_error": avg_error,
                        "target_boost": range_target.mean(),
                        "actual_boost": range_actual.mean(),
                        "duty_adjustment": duty_adjustment,
                        "data_points": len(range_error)
                    })

        return results

    def _detect_boost_spikes(self, df: pd.DataFrame) -> Dict:
        """Detect boost spikes"""
        boost_data = df["Manifold Absolute Pressure (psi)"] - 14.7

        # Simple spike detection - look for rapid increases
        boost_diff = boost_data.diff()
        spikes = boost_diff[boost_diff > 3]  # >3 psi rapid increase

        result = {
            "spikes_detected": len(spikes) > 0,
            "spike_count": len(spikes),
            "max_spike": spikes.max() if len(spikes) > 0 else 0,
            "total_points": len(boost_data)
        }

        if len(spikes) > 0 and "Engine Speed (rpm)" in df.columns:
            spike_rpms = df.loc[spikes.index, "Engine Speed (rpm)"]
            result["spike_rpm_range"] = f"{spike_rpms.min():.0f}-{spike_rpms.max():.0f}"
        else:
            result["spike_rpm_range"] = "Unknown"

        return result

    def _analyze_idle_conditions(self, df: pd.DataFrame) -> Dict:
        """Analyze idle conditions"""
        if "Engine Speed (rpm)" not in df.columns:
            return {"issues_found": False}

        idle_data = df[df["Engine Speed (rpm)"] < 1200]

        if len(idle_data) < 20:
            return {"issues_found": False}

        rpm_variation = idle_data["Engine Speed (rpm)"].std()
        avg_idle = idle_data["Engine Speed (rpm)"].mean()

        issues_found = rpm_variation > 50  # More than 50 RPM variation

        return {
            "issues_found": issues_found,
            "rpm_variation": rpm_variation,
            "avg_idle": avg_idle,
            "target_idle": 750,
            "data_points": len(idle_data),
            "description": f"Idle RPM variation: ±{rpm_variation:.0f} RPM",
            "recommendation": "Adjust idle speed control parameters" if issues_found else "Idle appears stable"
        }

    def _analyze_part_throttle(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze part throttle conditions"""
        results = []

        if "Manifold Absolute Pressure (psi)" not in df.columns or "A/F Sensor #1 (AFR)" not in df.columns:
            return results

        # Define part throttle load ranges
        load_ranges = [(0, 5), (5, 10)]

        for load_range in load_ranges:
            load_data = df["Manifold Absolute Pressure (psi)"] - 14.7
            load_mask = (load_data >= load_range[0]) & (load_data < load_range[1])
            range_data = df[load_mask]

            if len(range_data) > 20:
                avg_afr = range_data["A/F Sensor #1 (AFR)"].mean()
                target_afr = 14.7 if load_range[1] <= 5 else 13.8

                afr_error = avg_afr - target_afr
                fuel_adjustment = (afr_error / target_afr) * 100 * -1

                optimization_needed = abs(afr_error) > 0.3

                results.append({
                    "load_range": f"{load_range[0]:+.1f} to {load_range[1]:+.1f} psi",
                    "rpm_range": "2000-4000",
                    "avg_afr": avg_afr,
                    "target_afr": target_afr,
                    "fuel_adjustment": fuel_adjustment,
                    "optimization_needed": optimization_needed,
                    "data_points": len(range_data),
                    "confidence": "high" if len(range_data) > 50 else "medium",
                    "recommendation": f"Adjust fuel by {fuel_adjustment:+.1f}% in part throttle" if optimization_needed else "Part throttle AFR optimal"
                })

        return results

    def _analyze_temperatures(self, df: pd.DataFrame) -> Dict:
        """Analyze temperature conditions"""
        temp_data = df["Coolant Temperature (F)"].dropna()
        max_temp = temp_data.max()
        high_temps = temp_data[temp_data > 220]

        return {
            "high_temps_detected": len(high_temps) > 0,
            "max_temp": max_temp,
            "high_temp_duration": len(high_temps) * 0.1,  # Assuming 10Hz logging
            "data_points": len(temp_data),
            "recommendation": "Improve cooling system or reduce load" if len(high_temps) > 0 else "Temperature management adequate"
        }

    def _analyze_enrichments_and_compensations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Evaluate warmup enrichment, tip-in enrichment and temperature compensations."""
        suggestions = []

        # Warmup enrichment analysis
        if "Coolant Temperature (F)" in df.columns and "A/F Sensor #1 (AFR)" in df.columns:
            warm_data = df[df["Coolant Temperature (F)"] < 120]
            if len(warm_data) > 10:
                avg_afr = warm_data["A/F Sensor #1 (AFR)"].mean()
                if avg_afr > 14.5:
                    suggestions.append({
                        "id": "warmup_enrichment_adjust",
                        "type": "Warmup Enrichment",
                        "priority": "medium",
                        "description": f"Lean warmup AFR {avg_afr:.1f} detected",
                        "specific_action": "Increase warmup enrichment",
                        "rpm_range": "idle-2500",
                        "load_range": "low load",
                        "confidence": round(min(1.0, len(warm_data) / 20), 2),
                        "data_points": len(warm_data),
                    })

        # Tip-in enrichment analysis using MAP spikes
        if "Manifold Absolute Pressure (psi)" in df.columns and "A/F Sensor #1 (AFR)" in df.columns:
            map_diff = df["Manifold Absolute Pressure (psi)"].diff()
            spike_idx = map_diff[map_diff > 3].index
            lean_events = 0
            for idx in spike_idx:
                afr_window = df["A/F Sensor #1 (AFR)"].iloc[idx : idx + 3]
                if len(afr_window) > 0 and afr_window.min() > 14.7:
                    lean_events += 1
            if lean_events > 3:
                suggestions.append({
                    "id": "tip_in_enrichment",
                    "type": "Tip-In Enrichment",
                    "priority": "medium",
                    "description": f"{lean_events} lean tip-in events detected",
                    "specific_action": "Increase tip-in enrichment",
                    "rpm_range": "various",
                    "load_range": "rapid throttle",
                    "confidence": round(min(1.0, lean_events / 5), 2),
                    "data_points": lean_events,
                })

        # Temperature compensation consistency
        if "A/F Correction #1 (%)" in df.columns and "Intake Air Temperature (F)" in df.columns:
            cold = df[df["Intake Air Temperature (F)"] < 60]["A/F Correction #1 (%)"]
            hot = df[df["Intake Air Temperature (F)"] > 90]["A/F Correction #1 (%)"]
            if len(cold) > 5 and len(hot) > 5:
                cold_avg = cold.mean()
                hot_avg = hot.mean()
                if abs(cold_avg - hot_avg) > 5:
                    action = "increase" if cold_avg > hot_avg else "decrease"
                    confidence = round(min(1.0, abs(cold_avg - hot_avg) / 10), 2)

                    suggestions.append({
                        "id": "iat_compensation",
                        "type": "Temperature Compensation",
                        "priority": "low",
                        "description": "A/F corrections vary with intake temperature",
                        "specific_action": f"{action.capitalize()} IAT fuel compensation",
                        "rpm_range": "various",
                        "load_range": "various",
                        "confidence": confidence,
                        "data_points": int(len(cold) + len(hot)),
                    })

        return suggestions

    def _analyze_avcs_performance(self, df: pd.DataFrame) -> Dict:
        """Analyze AVCS performance (Subaru specific)"""
        if "AVCS Intake Position (degrees)" not in df.columns:
            return {"optimization_available": False}

        avcs_data = df["AVCS Intake Position (degrees)"].dropna()

        # Simple analysis - look for mid-range optimization
        if "Engine Speed (rpm)" in df.columns:
            mid_range_mask = (df["Engine Speed (rpm)"] >= 2500) & (df["Engine Speed (rpm)"] <= 4000)
            mid_range_avcs = avcs_data[mid_range_mask]

            if len(mid_range_avcs) > 20:
                avg_position = mid_range_avcs.mean()

                # Conservative optimization
                optimization_available = avg_position < 10  # Conservative AVCS position
                recommended_adjustment = 5 if optimization_available else 0

                return {
                    "optimization_available": optimization_available,
                    "rpm_range": "2500-4000",
                    "load_range": "Mid-range",
                    "avg_position": avg_position,
                    "recommended_position": avg_position + recommended_adjustment,
                    "recommended_adjustment": recommended_adjustment,
                    "estimated_gain": "+3-5% mid-range torque",
                    "data_points": len(mid_range_avcs)
                }

        return {"optimization_available": False}

    def _analyze_fuel_learning(self, df: pd.DataFrame) -> Dict:
        """Analyze fuel learning (Subaru specific)"""
        learning_data = df["A/F Learning #1 (%)"].dropna()
        max_learning = learning_data.max()
        min_learning = learning_data.min()
        avg_learning = learning_data.mean()

        excessive_learning = max(abs(max_learning), abs(min_learning)) > 15

        return {
            "excessive_learning": excessive_learning,
            "max_learning": max_learning,
            "min_learning": min_learning,
            "avg_learning": avg_learning,
            "affected_areas": "Areas with high learning values",
            "data_points": len(learning_data)
        }

    def _analyze_vtec_transition(self, df: pd.DataFrame) -> Dict:
        """Analyze VTEC transition (Honda specific)"""
        # Simplified VTEC analysis
        rpm_data = df["Engine Speed (rpm)"].dropna()
        high_rpm_data = rpm_data[rpm_data > 5000]

        if len(high_rpm_data) > 20:
            return {
                "optimization_needed": True,
                "transition_rpm": 5800,
                "current_behavior": "Standard VTEC engagement",
                "recommended_change": "Optimize VTEC transition timing",
                "data_points": len(high_rpm_data)
            }

        return {"optimization_needed": False}

    def _analyze_trend_patterns(self, df: pd.DataFrame, interval_size: int) -> List[Dict[str, Any]]:
        """Analyze trends across RPM intervals using simple heuristics."""
        results: List[Dict[str, Any]] = []

        rpm_col = "Engine Speed (rpm)"
        if rpm_col not in df.columns:
            return results

        load_col, load_unit = self._determine_load_info(df)

        rpm_min = int(df[rpm_col].min())
        rpm_max = int(df[rpm_col].max()) + interval_size
        intervals = list(range(rpm_min - rpm_min % interval_size, rpm_max, interval_size))

        th = self.trend_thresholds
        min_pts = int(th.get("min_interval_points", 5))
        lean_delta = th.get("lean_delta", 0.3)
        lean_afr = th.get("lean_afr_threshold", 14.7)
        load_delta = th.get("load_rise_delta", 3.0)

        prev_metrics = None
        for start in intervals[:-1]:
            end = start + interval_size
            seg = df[(df[rpm_col] >= start) & (df[rpm_col] < end)]
            if len(seg) < min_pts:
                continue

            metrics = {
                "avg_afr": seg["A/F Sensor #1 (AFR)"].mean() if "A/F Sensor #1 (AFR)" in seg.columns else None,
                "knock_events": seg["Knock Sum"][seg["Knock Sum"] > 0].count() if "Knock Sum" in seg.columns else 0,
                "avg_load": seg[load_col].mean() if load_col and load_col in seg.columns else None,
                "load_min": seg[load_col].min() if load_col and load_col in seg.columns else None,
                "load_max": seg[load_col].max() if load_col and load_col in seg.columns else None,
                "avg_timing": seg["Ignition Total Timing (degrees)"].mean() if "Ignition Total Timing (degrees)" in seg.columns else None,
                "data_points": len(seg),
            }

            if prev_metrics:
                if metrics["avg_afr"] and prev_metrics.get("avg_afr"):
                    if metrics["avg_afr"] - prev_metrics["avg_afr"] > lean_delta and metrics["avg_afr"] > lean_afr:
                        load_desc = self._format_load_range(
                            metrics["load_min"], metrics["load_max"], load_unit
                        )
                        results.append({
                            "rpm_range": f"{start}-{end}",
                            "load_range": load_desc,
                            "suggestion": "Increase fuel",
                            "reason": "AFR trending lean compared to previous interval",
                            "confidence": round(min(1.0, metrics["data_points"] / 20), 2),
                            "data_points": metrics["data_points"],
                        })

                if metrics["knock_events"] > prev_metrics.get("knock_events", 0) and metrics["knock_events"] > 0:
                    load_desc = self._format_load_range(
                        metrics["load_min"], metrics["load_max"], load_unit
                    )
                    results.append({
                        "rpm_range": f"{start}-{end}",
                        "load_range": load_desc,
                        "suggestion": "Reduce ignition timing",
                        "reason": f"Knock count increased to {metrics['knock_events']} in this interval",
                        "confidence": round(min(1.0, metrics["data_points"] / 20), 2),
                        "data_points": metrics["data_points"],
                    })

                if metrics["avg_load"] and prev_metrics.get("avg_load"):
                    if metrics["avg_load"] - prev_metrics["avg_load"] > load_delta:
                        load_desc = self._format_load_range(
                            metrics["load_min"], metrics["load_max"], load_unit
                        )
                        results.append({
                            "rpm_range": f"{start}-{end}",
                            "load_range": load_desc,
                            "suggestion": "Reduce boost or wastegate duty",
                            "reason": "Load rising quickly compared to previous interval",
                            "confidence": round(min(1.0, metrics["data_points"] / 20), 2),
                            "data_points": metrics["data_points"],
                        })

            prev_metrics = metrics

        return results

    def _group_suggestions_by_intervals(
        self,
        suggestions: List[Dict[str, Any]],
        rpm_interval: int,
        load_interval: int,
        df: pd.DataFrame,
    ) -> List[Dict[str, Any]]:
        """Break suggestions into uniform RPM and load intervals."""

        grouped: List[Dict[str, Any]] = []

        _, load_unit = self._determine_load_info(df)

        for s in suggestions:
            rpm_range = s.get("rpm_range")
            load_range = s.get("load_range")

            rpm_start, rpm_end = self._parse_numeric_range(rpm_range)
            load_start, load_end = self._parse_numeric_range(load_range)

            rpm_chunks = self._split_range(rpm_start, rpm_end, rpm_interval)
            load_chunks = (
                self._split_range(load_start, load_end, load_interval)
                if load_start is not None and load_interval > 0
                else [(load_start, load_end)]
            )

            for r_start, r_end in rpm_chunks:
                for l_start, l_end in load_chunks:
                    entry = s.copy()
                    if r_start is not None:
                        entry["rpm_range"] = f"{int(r_start)}-{int(r_end)}"
                    if l_start is not None:
                        entry["load_range"] = self._format_load_range(
                            l_start, l_end, load_unit
                        )
                    grouped.append(entry)

        return grouped

    @staticmethod
    def _parse_numeric_range(range_str: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
        """Extract numeric start/end from a range string."""
        if not range_str:
            return None, None
        nums = re.findall(r"-?\d+\.?\d*", range_str)
        if not nums:
            return None, None
        if len(nums) == 1:
            val = float(nums[0])
            return val, val
        return float(nums[0]), float(nums[1])

    @staticmethod
    def _split_range(start: Optional[float], end: Optional[float], step: int) -> List[Tuple[Optional[float], Optional[float]]]:
        """Splits a numeric range into chunks of a given step size.

        Args:
            start: The start of the range.
            end: The end of the range.
            step: The size of each chunk.

        Returns:
            A list of ``(start, end)`` tuples representing the chunks.
        """
        if start is None or end is None:
            return [(start, end)]
        if start > end:
            start, end = end, start
        chunks = []
        cur = math.floor(start / step) * step
        while cur < end:
            next_end = cur + step
            sub_start = max(cur, start)
            sub_end = min(next_end, end)
            if sub_end > sub_start:
                chunks.append((sub_start, sub_end))
            cur = next_end
        return chunks if chunks else [(start, end)]

    @staticmethod
    def _format_load_range(load_min: Optional[float], load_max: Optional[float], unit: str) -> str:
        """Return a standardized load range string."""
        if load_min is None or load_max is None:
            return "N/A"
        value = f"{load_min:.1f}-{load_max:.1f}"
        return f"{value} {unit}" if unit else value

    @staticmethod
    def _determine_load_info(df: pd.DataFrame) -> Tuple[Optional[str], str]:
        if "Manifold Absolute Pressure (psi)" in df.columns:
            return "Manifold Absolute Pressure (psi)", "psi"
        if "Mass Airflow (g/s)" in df.columns:
            return "Mass Airflow (g/s)", "g/s"
        return None, ""

    def _generate_no_data_suggestions(self) -> List[Dict[str, Any]]:
        """Generate suggestions when no datalog data is available"""
        return [{
            "id": "no_data_available",
            "type": "Data Collection Required",
            "priority": "high",
            "description": "No datalog data available for analysis",
            "specific_action": "Collect comprehensive datalog data during various driving conditions",
            "parameter": "datalog_collection",
            "change_type": "data_collection",
            "affected_areas": "All systems",
            "safety_impact": "Cannot assess safety without data",
            "performance_impact": "Cannot optimize without baseline data",
            "validation_method": "Collect at least 5 minutes of varied driving data",
            "confidence": "high",
            "recommendations": [
                "Log during idle, cruise, and acceleration",
                "Include all critical parameters (AFR, knock, boost, temps)",
                "Ensure minimum 10Hz logging rate",
                "Drive in various load conditions"
            ]
        }]

# Usage example
if __name__ == "__main__":
    ai_engine = EnhancedTuningAI()
    # suggestions = ai_engine.generate_comprehensive_suggestions(analysis_data)

def generate_enhanced_ai_suggestions(
    analysis_data: Dict[str, Any],
    interval_size: int = 1000,
    load_interval_size: int = 5,
) -> List[Dict[str, Any]]:
    """Return interval-grouped tuning suggestions.

    Parameters
    ----------
    analysis_data : Dict[str, Any]
        Parsed datalog and tune information.
    interval_size : int, optional
        RPM grouping step (500 or 1000). Defaults to 1000.
    load_interval_size : int, optional
        Pressure or load grouping step. Defaults to 5.

    Returns
    -------
    List[Dict[str, Any]]
        Suggestions broken down by RPM and load range.
    """

    ai = EnhancedTuningAI()
    return ai.generate_comprehensive_suggestions(
        analysis_data, interval_size, load_interval_size
    )
