import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DatalogAnalyzer:
    """Advanced datalog analysis with real tuning insights"""

    def __init__(self):
        self.analysis_rules = {
            "lean_condition": {
                "column": "A/F Sensor #1 (AFR)",
                "threshold": 15.0,
                "severity": "critical",
                "description": "Lean air-fuel ratio detected"
            },
            "rich_condition": {
                "column": "A/F Sensor #1 (AFR)", 
                "threshold": 12.0,
                "severity": "medium",
                "description": "Rich air-fuel ratio detected"
            },
            "high_af_correction": {
                "column": "A/F Correction #1 (%)",
                "threshold": 15.0,
                "severity": "high",
                "description": "High A/F correction indicates fueling issues"
            },
            "knock_detected": {
                "column": "Knock Sum",
                "threshold": 1.0,
                "severity": "critical", 
                "description": "Engine knock detected"
            },
            "high_boost": {
                "column": "Manifold Absolute Pressure (psi)",
                "threshold": 25.0,
                "severity": "medium",
                "description": "High boost pressure detected"
            }
        }

    def analyze_datalog(self, datalog_path: str) -> Dict[str, Any]:
        """Comprehensive datalog analysis"""
        try:
            df = pd.read_csv(datalog_path)
            logger.info(f"Analyzing datalog: {len(df)} rows, {len(df.columns)} columns")

            # Basic summary
            summary = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns),
                "duration": self._calculate_duration(df),
                "rpm_range": self._get_rpm_range(df),
                "load_range": self._get_load_range(df),
                "temperature_range": self._get_temperature_range(df)
            }

            # Issue detection
            issues = self._detect_issues(df)

            # Performance analysis
            performance = self._analyze_performance(df)

            # Safety analysis
            safety = self._analyze_safety(df)

            # Generate tuning suggestions based on real data
            suggestions = self._generate_tuning_suggestions(df, issues)

            # Data quality assessment
            data_quality = self._assess_data_quality(df)

            return {
                "summary": summary,
                "issues": issues,
                "performance": performance,
                "safety": safety,
                "suggestions": suggestions,
                "data_quality": data_quality,
                "load_analysis": self._analyze_load_points(df)
            }

        except Exception as e:
            logger.error(f"Error analyzing datalog: {e}")
            raise

    def _calculate_duration(self, df: pd.DataFrame) -> float:
        """Calculate log duration in seconds"""
        if "Time (msec)" in df.columns and len(df) > 1:
            return (df["Time (msec)"].iloc[-1] - df["Time (msec)"].iloc[0]) / 1000.0
        return 0.0

    def _get_rpm_range(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get RPM range from datalog"""
        rpm_col = "Engine Speed (rpm)"
        if rpm_col in df.columns:
            return {
                "min": int(df[rpm_col].min()),
                "max": int(df[rpm_col].max()),
                "avg": int(df[rpm_col].mean())
            }
        return {"min": 0, "max": 0, "avg": 0}

    def _get_load_range(self, df: pd.DataFrame) -> Dict[str, float]:
        """Get load range from datalog"""
        load_col = "Manifold Absolute Pressure (psi)"
        if load_col in df.columns:
            # Convert to relative load (boost)
            boost_data = df[load_col] - 14.7
            return {
                "min": round(boost_data.min(), 2),
                "max": round(boost_data.max(), 2),
                "avg": round(boost_data.mean(), 2)
            }
        return {"min": 0.0, "max": 0.0, "avg": 0.0}

    def _get_temperature_range(self, df: pd.DataFrame) -> Dict[str, float]:
        """Get temperature range from datalog"""
        temp_col = "Coolant Temperature (F)"
        if temp_col in df.columns:
            return {
                "min": round(df[temp_col].min(), 1),
                "max": round(df[temp_col].max(), 1),
                "avg": round(df[temp_col].mean(), 1)
            }
        return {"min": 0.0, "max": 0.0, "avg": 0.0}

    def _detect_issues(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect tuning issues from datalog"""
        issues = []

        for issue_type, rule in self.analysis_rules.items():
            column = rule["column"]
            if column not in df.columns:
                continue

            if issue_type == "lean_condition":
                lean_count = len(df[df[column] > rule["threshold"]])
                if lean_count > 0:
                    issues.append({
                        "type": issue_type,
                        "severity": rule["severity"],
                        "count": lean_count,
                        "percentage": round((lean_count / len(df)) * 100, 2),
                        "message": f"Detected {lean_count} lean conditions (AFR > {rule['threshold']})",
                        "column": column,
                        "recommendation": "Enrich fuel map in affected RPM/load areas",
                        "affected_areas": self._get_affected_areas(df[df[column] > rule["threshold"]])
                    })

            elif issue_type == "rich_condition":
                rich_count = len(df[df[column] < rule["threshold"]])
                if rich_count > 0:
                    issues.append({
                        "type": issue_type,
                        "severity": rule["severity"],
                        "count": rich_count,
                        "percentage": round((rich_count / len(df)) * 100, 2),
                        "message": f"Detected {rich_count} rich conditions (AFR < {rule['threshold']})",
                        "column": column,
                        "recommendation": "Lean out fuel map in affected RPM/load areas",
                        "affected_areas": self._get_affected_areas(df[df[column] < rule["threshold"]])
                    })

            elif issue_type == "high_af_correction":
                high_corr_count = len(df[abs(df[column]) > rule["threshold"]])
                if high_corr_count > 0:
                    avg_correction = df[column].mean()
                    issues.append({
                        "type": issue_type,
                        "severity": rule["severity"],
                        "count": high_corr_count,
                        "percentage": round((high_corr_count / len(df)) * 100, 2),
                        "message": f"High A/F corrections detected (avg: {avg_correction:.1f}%)",
                        "column": column,
                        "recommendation": "Adjust base fuel map to reduce ECU corrections",
                        "affected_areas": self._get_affected_areas(df[abs(df[column]) > rule["threshold"]])
                    })

            elif issue_type == "knock_detected":
                knock_count = len(df[df[column] > rule["threshold"]])
                if knock_count > 0:
                    issues.append({
                        "type": issue_type,
                        "severity": rule["severity"],
                        "count": knock_count,
                        "percentage": round((knock_count / len(df)) * 100, 2),
                        "message": f"Knock detected in {knock_count} data points",
                        "column": column,
                        "recommendation": "Reduce ignition timing and/or boost pressure",
                        "affected_areas": self._get_affected_areas(df[df[column] > rule["threshold"]])
                    })

            elif issue_type == "high_boost":
                boost_data = df[column] - 14.7  # Convert to boost
                high_boost_count = len(boost_data[boost_data > rule["threshold"]])
                if high_boost_count > 0:
                    max_boost = boost_data.max()
                    issues.append({
                        "type": issue_type,
                        "severity": rule["severity"],
                        "count": high_boost_count,
                        "percentage": round((high_boost_count / len(df)) * 100, 2),
                        "message": f"High boost detected (max: {max_boost:.1f} psi)",
                        "column": column,
                        "recommendation": "Monitor for knock and adjust boost control if needed"
                    })

        return issues

    def _get_affected_areas(self, df_subset: pd.DataFrame) -> List[Dict]:
        """Get RPM/load areas affected by issues"""
        if len(df_subset) == 0:
            return []

        areas = []
        if "Engine Speed (rpm)" in df_subset.columns:
            rpm_data = df_subset["Engine Speed (rpm)"]
            areas.append({
                "parameter": "RPM",
                "min": int(rpm_data.min()),
                "max": int(rpm_data.max()),
                "data_points": len(rpm_data)
            })

        if "Manifold Absolute Pressure (psi)" in df_subset.columns:
            load_data = df_subset["Manifold Absolute Pressure (psi)"] - 14.7
            areas.append({
                "parameter": "Boost",
                "min": round(load_data.min(), 2),
                "max": round(load_data.max(), 2),
                "data_points": len(load_data)
            })

        return areas

    def _analyze_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance metrics"""
        performance = {}

        # Power estimation based on MAF
        if "Mass Airflow (g/s)" in df.columns:
            max_maf = df["Mass Airflow (g/s)"].max()
            estimated_hp = max_maf * 1.5  # Rough estimation
            performance["estimated_peak_hp"] = round(estimated_hp, 1)
            performance["max_maf"] = round(max_maf, 1)

        # Boost analysis
        if "Manifold Absolute Pressure (psi)" in df.columns:
            boost_data = df["Manifold Absolute Pressure (psi)"] - 14.7
            performance["max_boost"] = round(boost_data.max(), 1)
            performance["avg_boost"] = round(boost_data.mean(), 1)

        # Timing analysis
        if "Ignition Total Timing (degrees)" in df.columns:
            timing_data = df["Ignition Total Timing (degrees)"]
            performance["max_timing"] = round(timing_data.max(), 1)
            performance["avg_timing"] = round(timing_data.mean(), 1)

        # Duty cycle analysis
        if "Injector Duty Cycle (%)" in df.columns:
            duty_data = df["Injector Duty Cycle (%)"]
            performance["max_duty_cycle"] = round(duty_data.max(), 1)
            performance["avg_duty_cycle"] = round(duty_data.mean(), 1)

        return performance

    def _analyze_safety(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze safety metrics"""
        safety = {
            "overall_status": "safe",
            "critical_issues": [],
            "warnings": []
        }

        # Check for knock
        if "Knock Sum" in df.columns:
            knock_events = len(df[df["Knock Sum"] > 0])
            if knock_events > 0:
                safety["critical_issues"].append({
                    "type": "Knock Detected",
                    "message": f"{knock_events} knock events detected",
                    "severity": "critical"
                })
                safety["overall_status"] = "unsafe"

        # Check temperatures
        if "Coolant Temperature (F)" in df.columns:
            max_temp = df["Coolant Temperature (F)"].max()
            if max_temp > 220:
                safety["warnings"].append({
                    "type": "High Temperature",
                    "message": f"Maximum coolant temperature: {max_temp:.1f}°F",
                    "severity": "warning"
                })

        # Check boost levels
        if "Manifold Absolute Pressure (psi)" in df.columns:
            boost_data = df["Manifold Absolute Pressure (psi)"] - 14.7
            max_boost = boost_data.max()
            if max_boost > 20:
                safety["warnings"].append({
                    "type": "High Boost",
                    "message": f"Maximum boost pressure: {max_boost:.1f} psi",
                    "severity": "warning"
                })

        # Check duty cycle
        if "Injector Duty Cycle (%)" in df.columns:
            max_duty = df["Injector Duty Cycle (%)"].max()
            if max_duty > 85:
                safety["warnings"].append({
                    "type": "High Duty Cycle",
                    "message": f"Maximum injector duty cycle: {max_duty:.1f}%",
                    "severity": "warning"
                })

        return safety

    def _generate_tuning_suggestions(self, df: pd.DataFrame, issues: List[Dict]) -> List[Dict[str, Any]]:
        """Generate specific tuning suggestions based on datalog analysis"""
        suggestions = []

        # Fuel map suggestions based on AFR data
        if "A/F Sensor #1 (AFR)" in df.columns and "Engine Speed (rpm)" in df.columns:
            afr_data = df["A/F Sensor #1 (AFR)"]

            # Find lean areas
            lean_mask = afr_data > 15.0
            if lean_mask.any():
                lean_areas = self._get_affected_areas(df[lean_mask])
                suggestions.append({
                    "id": "fuel_enrichment_lean",
                    "type": "Fuel Map Enrichment",
                    "priority": "critical",
                    "table": "Primary_Open_Loop_Fueling",
                    "description": f"Enrich fuel map due to lean AFR conditions",
                    "affected_areas": lean_areas,
                    "change_type": "increase",
                    "percentage": 5,
                    "safety_impact": "Critical - prevents engine damage from lean conditions",
                    "performance_impact": "Safer operation, prevents detonation"
                })

        # A/F correction suggestions
        if "A/F Correction #1 (%)" in df.columns:
            af_corr = df["A/F Correction #1 (%)"]
            avg_correction = af_corr.mean()

            if abs(avg_correction) > 5:
                suggestions.append({
                    "id": "base_fuel_adjustment",
                    "type": "Base Fuel Map Adjustment", 
                    "priority": "high",
                    "table": "Primary_Open_Loop_Fueling",
                    "description": f"Adjust base fuel map to reduce ECU corrections (avg: {avg_correction:.1f}%)",
                    "change_type": "increase" if avg_correction > 0 else "decrease",
                    "percentage": abs(avg_correction) * 0.5,
                    "safety_impact": "Reduces ECU correction load",
                    "performance_impact": "More consistent fuel delivery"
                })

        # Ignition timing suggestions
        if "Knock Sum" in df.columns:
            knock_events = len(df[df["Knock Sum"] > 0])
            if knock_events > 0:
                suggestions.append({
                    "id": "timing_retard_knock",
                    "type": "Ignition Timing Reduction",
                    "priority": "critical",
                    "table": "Ignition_Timing_Base",
                    "description": f"Reduce ignition timing due to {knock_events} knock events",
                    "change_type": "decrease",
                    "percentage": 10,
                    "safety_impact": "Critical - prevents engine damage from knock",
                    "performance_impact": "Reduced power but safer operation"
                })

        # Add suggestions based on detected issues
        for issue in issues:
            if issue["type"] == "lean_condition":
                suggestions.append({
                    "id": f"issue_based_{issue['type']}",
                    "type": "Critical Fuel Adjustment",
                    "priority": "critical",
                    "table": "Primary_Open_Loop_Fueling",
                    "description": f"Addressing detected issue: {issue['message']}",
                    "change_type": "increase",
                    "percentage": 8,
                    "affected_areas": issue.get("affected_areas", []),
                    "safety_impact": "Critical - prevents engine damage",
                    "performance_impact": "Safer operation, consistent power delivery"
                })

        return suggestions

    def _analyze_load_points(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze load points for tuning coverage"""
        if "Engine Speed (rpm)" not in df.columns or "Manifold Absolute Pressure (psi)" not in df.columns:
            return {}

        rpm_data = df["Engine Speed (rpm)"]
        load_data = df["Manifold Absolute Pressure (psi)"] - 14.7  # Convert to boost

        # Define load point bins
        rpm_bins = [0, 1500, 2500, 3500, 4500, 5500, 7000]
        load_bins = [-5, 0, 5, 10, 15, 20, 30]

        load_points = {}
        for i in range(len(rpm_bins) - 1):
            for j in range(len(load_bins) - 1):
                rpm_mask = (rpm_data >= rpm_bins[i]) & (rpm_data < rpm_bins[i + 1])
                load_mask = (load_data >= load_bins[j]) & (load_data < load_bins[j + 1])
                combined_mask = rpm_mask & load_mask

                point_count = combined_mask.sum()
                if point_count > 0:
                    key = f"{rpm_bins[i]}-{rpm_bins[i+1]}rpm_{load_bins[j]}-{load_bins[j+1]}psi"
                    load_points[key] = {
                        "rpm_range": [rpm_bins[i], rpm_bins[i + 1]],
                        "load_range": [load_bins[j], load_bins[j + 1]],
                        "data_points": int(point_count),
                        "coverage": "good" if point_count > 10 else "limited"
                    }

        return {
            "total_load_points": len(load_points),
            "load_points": load_points,
            "coverage_summary": {
                "well_covered": len([lp for lp in load_points.values() if lp["coverage"] == "good"]),
                "limited_coverage": len([lp for lp in load_points.values() if lp["coverage"] == "limited"])
            }
        }

    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess datalog quality"""
        duration = self._calculate_duration(df)
        rpm_range = self._get_rpm_range(df)

        return {
            "completeness": round((df.count().sum() / (len(df) * len(df.columns))) * 100, 1),
            "duration_adequate": duration > 30,  # At least 30 seconds
            "rpm_coverage": "excellent" if rpm_range["max"] > 5000 else "good" if rpm_range["max"] > 3000 else "limited",
            "data_density": "high" if len(df) > 1000 else "medium" if len(df) > 500 else "low",
            "missing_critical_params": self._check_missing_params(df)
        }

    def _check_missing_params(self, df: pd.DataFrame) -> List[str]:
        """Check for missing critical parameters"""
        critical_params = [
            "A/F Sensor #1 (AFR)",
            "Engine Speed (rpm)",
            "Manifold Absolute Pressure (psi)",
            "Coolant Temperature (F)",
            "Mass Airflow (g/s)"
        ]

        missing = []
        for param in critical_params:
            if param not in df.columns:
                missing.append(param)

        return missing