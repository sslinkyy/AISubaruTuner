import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class TuningEngine:
    """Production-ready tuning engine with XML definition and ROM analysis support"""

    def __init__(self):
        self.safety_limits = {
            "max_fuel_change_percent": 15.0,
            "max_timing_change_degrees": 5.0,
            "max_boost_change_psi": 3.0,
            "max_afr_change": 1.0,
            "critical_afr_threshold": 11.5,
            "lean_afr_threshold": 15.5
        }

        # Table priority mapping for safety
        self.table_priorities = {
            "Primary Open Loop Fueling": "critical",
            "Base Fuel Map": "critical", 
            "Base Ignition Timing": "high",
            "Boost Control": "high",
            "A/F Learning": "medium",
            "Idle Speed Target": "low"
        }

        # Common table name mappings
        self.table_mappings = {
            "fuel": ["Primary Open Loop Fueling", "Base Fuel Map", "Fuel Map", "Injector Pulse Width"],
            "timing": ["Base Ignition Timing", "Ignition Timing", "Timing Map"],
            "boost": ["Boost Control", "Wastegate Control", "Target Boost"],
            "afr": ["A/F Learning", "Air Fuel Ratio", "Lambda Target"]
        }

    def _validate_inputs(
        self,
        rom_data: Dict,
        datalog_analysis: Dict,
        suggestions: List[Dict],
    ) -> Tuple[bool, str]:
        """Validate inputs before generating tune changes."""

        if not isinstance(rom_data, dict) or not rom_data.get("tables"):
            return False, "ROM data missing or invalid"

        if not isinstance(datalog_analysis, dict) or "summary" not in datalog_analysis:
            return False, "Datalog analysis missing or invalid"

        if not isinstance(suggestions, list):
            return False, "Suggestions must be a list"

        return True, ""

    def generate_tune_changes(
        self, rom_data: Dict, datalog_analysis: Dict, suggestions: List[Dict]
    ) -> Dict[str, Any]:
        """Generate specific tune changes based on ROM analysis and datalog data"""

        valid, message = self._validate_inputs(rom_data, datalog_analysis, suggestions)
        if not valid:
            logger.warning(f"Input validation failed: {message}")
            placeholder = self._generate_placeholder_changes(suggestions)
            placeholder["validation"] = {"status": "invalid", "message": message}
            return placeholder

        logger.info(
            f"Generating tune changes from {len(rom_data['tables'])} ROM tables and {len(suggestions)} suggestions"
        )
        logger.debug(
            "Input summary: tables=%s suggestions=%s issues=%s",
            len(rom_data.get("tables", {})),
            len(suggestions),
            len(datalog_analysis.get("issues", [])),
        )

        changes = []
        safety_warnings = []

        # Process each suggestion
        for suggestion in suggestions:
            try:
                change = self._process_suggestion(rom_data, suggestion, datalog_analysis)
                if change:
                    changes.append(change)

                    # Collect safety warnings
                    if change.get("safety_check", {}).get("warnings"):
                        safety_warnings.extend(change["safety_check"]["warnings"])

            except Exception as e:
                logger.error(f"Failed to process suggestion {suggestion.get('id', 'unknown')}: {e}")
                continue

        # Generate comprehensive result
        result = {
            "total_changes": len(changes),
            "changes": changes,
            "estimated_power_gain": self._estimate_power_gain(changes),
            "safety_rating": self._assess_safety_rating(changes),
            "validation": self._validate_changes(changes),
            "safety_warnings": list(set(safety_warnings)),  # Remove duplicates
            "rom_compatibility": self._assess_rom_compatibility(rom_data),
            "change_summary": self._generate_change_summary(changes),
            "generated_at": datetime.utcnow().isoformat(),
            "engine_version": "3.0.0"
        }

        logger.info(f"Generated {len(changes)} tune changes with safety rating: {result['safety_rating']}")
        return result

    def _process_suggestion(self, rom_data: Dict, suggestion: Dict, datalog_analysis: Dict) -> Optional[Dict[str, Any]]:
        """Process a single suggestion into tune changes"""

        # Find matching table in ROM
        target_table = self._find_target_table(rom_data, suggestion)

        if target_table:
            return self._generate_rom_based_change(target_table, suggestion, datalog_analysis)
        else:
            # Generate generic change if table not found
            logger.warning(f"Table not found for suggestion: {suggestion.get('table', 'unknown')}")
            return self._generate_generic_change(suggestion)

    def _find_target_table(self, rom_data: Dict, suggestion: Dict) -> Optional[Dict[str, Any]]:
        """Find the target table in ROM data for a suggestion"""

        target_table_name = suggestion.get("table", "")
        tables = rom_data.get("tables", {})

        # Direct name match
        if target_table_name in tables:
            return tables[target_table_name]

        # Fuzzy matching for common variations
        suggestion_type = suggestion.get("type", "").lower()

        for category, table_names in self.table_mappings.items():
            if category in suggestion_type:
                for table_name in table_names:
                    if table_name in tables:
                        logger.info(f"Mapped suggestion type '{suggestion_type}' to table '{table_name}'")
                        return tables[table_name]

        # Partial name matching
        for table_name, table_data in tables.items():
            if any(keyword in table_name.lower() for keyword in target_table_name.lower().split()):
                logger.info(f"Partial match: '{target_table_name}' -> '{table_name}'")
                return table_data

        return None

    def _generate_rom_based_change(self, table_data: Dict, suggestion: Dict, datalog_analysis: Dict) -> Dict[str, Any]:
        """Generate changes based on actual ROM table data"""

        try:
            # Get table information
            table_name = table_data["name"]
            data = table_data["data"]
            definition = table_data["definition"]

            if not data or not isinstance(data, list):
                logger.warning(f"Invalid table data for {table_name}")
                return self._generate_generic_change(suggestion)

            # Identify affected cells
            affected_cells = self._identify_affected_cells_advanced(table_data, suggestion, datalog_analysis)

            if not affected_cells:
                logger.warning(f"No affected cells identified for {table_name}")
                return None

            # Calculate changes for each cell
            cell_changes = []
            old_values = []
            new_values = []

            for cell in affected_cells:
                row, col = cell["row"], cell["col"]

                # Validate cell coordinates
                if row >= len(data) or col >= len(data[0]):
                    continue

                old_value = data[row][col]

                # Calculate new value based on suggestion and datalog analysis
                new_value = self._calculate_optimized_value(old_value, suggestion, cell, datalog_analysis)

                # Apply safety limits
                new_value = self._apply_advanced_safety_limits(old_value, new_value, suggestion, table_name)

                old_values.append(old_value)
                new_values.append(new_value)

                # Get axis values for context
                rpm_value = self._get_axis_value(table_data, "rpm_axis", row)
                load_value = self._get_axis_value(table_data, "load_axis", col)

                cell_changes.append({
                    "row": row,
                    "col": col,
                    "rpm": rpm_value,
                    "load": load_value,
                    "old_value": round(old_value, 4),
                    "new_value": round(new_value, 4),
                    "change_percent": round(((new_value - old_value) / old_value) * 100, 2) if old_value != 0 else 0,
                    "change_absolute": round(new_value - old_value, 4),
                    "confidence": cell.get("confidence", "medium"),
                    "reason": cell.get("reason", "General optimization")
                })

            # Generate comprehensive change record
            return {
                "id": suggestion.get("id", f"change_{table_name}"),
                "table_name": table_name,
                "table_description": definition.get("description", ""),
                "table_address": table_data.get("address", "unknown"),
                "change_type": suggestion.get("change_type", "optimization"),
                "priority": self._get_table_priority(table_name),
                "description": suggestion.get("description", f"Optimize {table_name}"),
                "affected_cells": len(cell_changes),
                "cell_changes": cell_changes,
                "summary": {
                    "old_range": f"{min(old_values):.4f} - {max(old_values):.4f}" if old_values else "N/A",
                    "new_range": f"{min(new_values):.4f} - {max(new_values):.4f}" if new_values else "N/A",
                    "avg_change": f"{np.mean([c['change_percent'] for c in cell_changes]):+.2f}%" if cell_changes else "0%",
                    "max_change": f"{max([abs(c['change_percent']) for c in cell_changes]):.2f}%" if cell_changes else "0%",
                    "total_cells": len(cell_changes)
                },
                "safety_check": self._perform_comprehensive_safety_check(suggestion, cell_changes, table_name),
                "units": definition.get("scaling", {}).get("units", ""),
                "scaling_applied": definition.get("scaling", {}).get("to_real", "x") != "x",
                "datalog_correlation": self._analyze_datalog_correlation(cell_changes, datalog_analysis),
                "rom_metadata": {
                    "storage_type": definition.get("storagetype", "unknown"),
                    "table_size": f"{definition.get('sizex', 0)}x{definition.get('sizey', 0)}",
                    "endianness": definition.get("endian", "unknown")
                },
                "predicted_effect": {
                    "performance": suggestion.get("performance_impact"),
                    "safety": suggestion.get("safety_impact")
                }
            }

        except Exception as e:
            logger.error(f"Error generating ROM-based change: {e}")
            return self._generate_generic_change(suggestion)

    def _identify_affected_cells_advanced(self, table_data: Dict, suggestion: Dict, datalog_analysis: Dict) -> List[Dict]:
        """Advanced cell identification based on datalog analysis"""

        cells = []
        data = table_data["data"]
        rows, cols = len(data), len(data[0]) if data else 0

        # Get RPM and load ranges from datalog analysis
        rpm_ranges = self._extract_rpm_ranges(datalog_analysis)
        load_ranges = self._extract_load_ranges(datalog_analysis)

        # Map datalog ranges to table cells
        rpm_axis = table_data.get("rpm_axis", list(range(rows)))
        load_axis = table_data.get("load_axis", list(range(cols)))

        for rpm_range in rpm_ranges:
            for load_range in load_ranges:
                # Find corresponding table cells
                for row, rpm in enumerate(rpm_axis):
                    if rpm_range["min"] <= rpm <= rpm_range["max"]:
                        for col, load in enumerate(load_axis):
                            if load_range["min"] <= load <= load_range["max"]:

                                # Calculate confidence based on datalog data density
                                confidence = self._calculate_cell_confidence(rpm, load, datalog_analysis)

                                cells.append({
                                    "row": row,
                                    "col": col,
                                    "rpm": rpm,
                                    "load": load,
                                    "confidence": confidence,
                                    "reason": f"Datalog activity in RPM {rpm_range['min']}-{rpm_range['max']}, Load {load_range['min']}-{load_range['max']}"
                                })

        # If no datalog-based cells found, use suggestion-based approach
        if not cells:
            cells = self._get_default_affected_cells(table_data, suggestion)

        # Limit and sort by confidence
        cells.sort(key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(x["confidence"], 1), reverse=True)
        return cells[:30]  # Limit to 30 cells max

    def _extract_rpm_ranges(self, datalog_analysis: Dict) -> List[Dict]:
        """Extract RPM ranges from datalog analysis"""

        # Default ranges if no specific analysis available
        default_ranges = [
            {"min": 2000, "max": 4000, "activity": "medium"},
            {"min": 4000, "max": 6000, "activity": "high"},
            {"min": 6000, "max": 8000, "activity": "low"}
        ]

        # Try to extract from actual datalog analysis
        if "load_analysis" in datalog_analysis:
            load_analysis = datalog_analysis["load_analysis"]
            if "rpm_ranges" in load_analysis:
                return load_analysis["rpm_ranges"]

        return default_ranges

    def _extract_load_ranges(self, datalog_analysis: Dict) -> List[Dict]:
        """Extract load ranges from datalog analysis"""

        # Default ranges
        default_ranges = [
            {"min": 0.5, "max": 1.5, "activity": "medium"},
            {"min": 1.5, "max": 2.5, "activity": "high"},
            {"min": 2.5, "max": 3.5, "activity": "low"}
        ]

        # Try to extract from actual datalog analysis
        if "load_analysis" in datalog_analysis:
            load_analysis = datalog_analysis["load_analysis"]
            if "load_ranges" in load_analysis:
                return load_analysis["load_ranges"]

        return default_ranges

    def _calculate_cell_confidence(self, rpm: float, load: float, datalog_analysis: Dict) -> str:
        """Calculate confidence level for a table cell based on datalog data"""

        # Default medium confidence
        confidence = "medium"

        # Check if this RPM/load combination appears frequently in datalog
        if "performance" in datalog_analysis:
            perf = datalog_analysis["performance"]

            # High confidence for frequently used areas
            if perf.get("avg_rpm", 0) * 0.8 <= rpm <= perf.get("avg_rpm", 0) * 1.2:
                confidence = "high"

            # Low confidence for extreme values
            if rpm > perf.get("max_rpm", 8000) * 0.9 or load > 3.0:
                confidence = "low"

        return confidence

    def _get_default_affected_cells(self, table_data: Dict, suggestion: Dict) -> List[Dict]:
        """Get default affected cells when datalog analysis is insufficient"""

        cells = []
        data = table_data["data"]
        rows, cols = len(data), len(data[0]) if data else 0

        suggestion_type = suggestion.get("type", "").lower()

        if "fuel" in suggestion_type:
            # Focus on mid-range for fuel changes
            start_row, end_row = max(0, rows//4), min(rows, 3*rows//4)
            start_col, end_col = max(0, cols//4), min(cols, 3*cols//4)
        elif "timing" in suggestion_type:
            # More conservative area for timing
            start_row, end_row = max(0, rows//3), min(rows, 2*rows//3)
            start_col, end_col = max(0, cols//3), min(cols, 2*cols//3)
        else:
            # Default area
            start_row, end_row = max(0, rows//4), min(rows, 3*rows//4)
            start_col, end_col = max(0, cols//4), min(cols, 3*cols//4)

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                cells.append({
                    "row": row,
                    "col": col,
                    "confidence": "medium",
                    "reason": f"Default {suggestion_type} optimization area"
                })

        return cells

    def _calculate_optimized_value(self, old_value: float, suggestion: Dict, cell: Dict, datalog_analysis: Dict) -> float:
        """Calculate optimized value based on multiple factors"""

        change_type = suggestion.get("change_type", "increase")
        base_percentage = suggestion.get("percentage", 5.0)

        # Adjust percentage based on cell confidence
        confidence_multiplier = {"high": 1.2, "medium": 1.0, "low": 0.7}.get(cell["confidence"], 1.0)
        adjusted_percentage = base_percentage * confidence_multiplier

        # Apply datalog-based adjustments
        if "issues" in datalog_analysis:
            for issue in datalog_analysis["issues"]:
                if issue.get("severity") == "critical":
                    adjusted_percentage *= 1.3  # More aggressive for critical issues
                elif issue.get("severity") == "low":
                    adjusted_percentage *= 0.8  # More conservative for minor issues

        # Calculate new value
        if change_type == "increase":
            return old_value * (1 + adjusted_percentage / 100)
        elif change_type == "decrease":
            return old_value * (1 - adjusted_percentage / 100)
        else:  # optimize
            # Smart optimization based on value range
            if old_value < 50:  # Likely a small value, increase slightly
                return old_value * 1.05
            else:  # Larger value, adjust more conservatively
                return old_value * 1.02

    def _apply_advanced_safety_limits(self, old_value: float, new_value: float, suggestion: Dict, table_name: str) -> float:
        """Apply advanced safety limits based on table type and value ranges"""

        table_type = table_name.lower()

        # Fuel table safety limits
        if any(keyword in table_type for keyword in ["fuel", "injector", "pulse"]):
            max_change = self.safety_limits["max_fuel_change_percent"]

            # More restrictive for lean conditions
            if suggestion.get("type", "").lower() == "lean":
                max_change *= 0.7

            return self._apply_percentage_limit(old_value, new_value, max_change)

        # Timing table safety limits
        elif any(keyword in table_type for keyword in ["timing", "ignition"]):
            max_change = self.safety_limits["max_timing_change_degrees"]

            # Absolute value limit for timing
            if abs(new_value - old_value) > max_change:
                return old_value + (max_change if new_value > old_value else -max_change)

        # Boost control safety limits
        elif any(keyword in table_type for keyword in ["boost", "wastegate"]):
            max_change = self.safety_limits["max_boost_change_psi"]
            return self._apply_percentage_limit(old_value, new_value, 20.0)  # 20% max for boost

        # AFR safety limits
        elif any(keyword in table_type for keyword in ["afr", "lambda", "air"]):
            # Prevent dangerous lean conditions
            if new_value > self.safety_limits["lean_afr_threshold"]:
                return self.safety_limits["lean_afr_threshold"]
            # Prevent overly rich conditions
            elif new_value < self.safety_limits["critical_afr_threshold"]:
                return self.safety_limits["critical_afr_threshold"]

        return new_value

    def _apply_percentage_limit(self, old_value: float, new_value: float, max_percentage: float) -> float:
        """Apply percentage-based safety limit"""
        max_ratio = 1 + max_percentage / 100
        min_ratio = 1 - max_percentage / 100

        if new_value > old_value * max_ratio:
            return old_value * max_ratio
        elif new_value < old_value * min_ratio:
            return old_value * min_ratio

        return new_value

    def _get_axis_value(self, table_data: Dict, axis_name: str, index: int) -> float:
        """Get axis value at specific index"""
        axis = table_data.get(axis_name, [])
        if axis and 0 <= index < len(axis):
            return axis[index]
        return float(index)  # Fallback to index

    def _get_table_priority(self, table_name: str) -> str:
        """Get priority level for table"""
        table_lower = table_name.lower()

        for priority, keywords in {
            "critical": ["fuel", "primary", "base fuel"],
            "high": ["timing", "ignition", "boost"],
            "medium": ["learning", "correction"],
            "low": ["idle", "fan", "misc"]
        }.items():
            if any(keyword in table_lower for keyword in keywords):
                return priority

        return "medium"  # Default priority

    def _perform_comprehensive_safety_check(self, suggestion: Dict, cell_changes: List[Dict], table_name: str) -> Dict[str, Any]:
        """Perform comprehensive safety check"""

        safety_check = {
            "status": "safe",
            "warnings": [],
            "critical_issues": [],
            "max_change_percent": 0,
            "risk_level": "low"
        }

        if not cell_changes:
            return safety_check

        # Calculate statistics
        change_percentages = [abs(c["change_percent"]) for c in cell_changes]
        max_change = max(change_percentages)
        avg_change = np.mean(change_percentages)

        safety_check["max_change_percent"] = max_change
        safety_check["avg_change_percent"] = avg_change

        # Check for excessive changes
        if max_change > 20:
            safety_check["critical_issues"].append(f"Excessive change detected: {max_change:.1f}%")
            safety_check["status"] = "critical"
            safety_check["risk_level"] = "high"
        elif max_change > 15:
            safety_check["warnings"].append(f"Large change detected: {max_change:.1f}%")
            safety_check["status"] = "caution"
            safety_check["risk_level"] = "medium"
        elif max_change > 10:
            safety_check["warnings"].append(f"Moderate change detected: {max_change:.1f}%")

        # Table-specific safety checks
        table_lower = table_name.lower()

        if "fuel" in table_lower and max_change > 12:
            safety_check["warnings"].append("Large fuel change - monitor AFR closely")

        if "timing" in table_lower and max_change > 8:
            safety_check["warnings"].append("Significant timing change - monitor for knock")

        if "boost" in table_lower and max_change > 15:
            safety_check["critical_issues"].append("Large boost change - check hardware limits")
            safety_check["status"] = "critical"

        # Check for too many high-impact changes
        high_impact_changes = sum(1 for c in change_percentages if c > 10)
        if high_impact_changes > 10:
            safety_check["warnings"].append(f"{high_impact_changes} high-impact changes - consider incremental approach")

        return safety_check

    def _analyze_datalog_correlation(self, cell_changes: List[Dict], datalog_analysis: Dict) -> Dict[str, Any]:
        """Analyze correlation between changes and datalog data"""

        correlation = {
            "confidence": "medium",
            "supporting_data": [],
            "concerns": []
        }

        # Check if changes align with datalog issues
        if "issues" in datalog_analysis:
            for issue in datalog_analysis["issues"]:
                if any(issue.get("parameter", "").lower() in str(change).lower() for change in cell_changes):
                    correlation["supporting_data"].append(f"Addresses {issue.get('type', 'issue')} in datalog")
                    correlation["confidence"] = "high"

        # Check for potential conflicts
        if "safety" in datalog_analysis:
            safety_issues = datalog_analysis["safety"].get("critical_issues", [])
            if safety_issues and len(cell_changes) > 15:
                correlation["concerns"].append("Many changes proposed despite safety issues")
                correlation["confidence"] = "low"

        return correlation

    def _generate_generic_change(self, suggestion: Dict) -> Dict[str, Any]:
        """Generate generic change when ROM table not available"""

        return {
            "id": suggestion.get("id", "generic_change"),
            "table_name": suggestion.get("table", "Unknown_Table"),
            "table_description": f"Generic change for {suggestion.get('type', 'optimization')}",
            "change_type": suggestion.get("change_type", "optimization"),
            "priority": suggestion.get("priority", "medium"),
            "description": suggestion.get("description", "Generic optimization"),
            "affected_cells": 10,  # Placeholder
            "cell_changes": [],
            "summary": {
                "old_range": "Various values",
                "new_range": "Adjusted values",
                "avg_change": f"{suggestion.get('percentage', 5):+.1f}%",
                "total_cells": 10
            },
            "safety_check": {
                "status": "safe",
                "warnings": ["Generic change - ROM analysis not available"],
                "max_change_percent": suggestion.get("percentage", 5)
            },
            "note": "Generic change - upload ROM file with XML definition for detailed analysis",
            "rom_metadata": {"status": "not_available"},
            "predicted_effect": {
                "performance": suggestion.get("performance_impact"),
                "safety": suggestion.get("safety_impact")
            }
        }

    def _generate_placeholder_changes(self, suggestions: List[Dict]) -> Dict[str, Any]:
        """Generate placeholder changes when no ROM data available"""

        changes = [self._generate_generic_change(suggestion) for suggestion in suggestions]

        return {
            "total_changes": len(changes),
            "changes": changes,
            "estimated_power_gain": self._estimate_power_gain(changes),
            "safety_rating": "Limited Analysis",
            "validation": {
                "status": "limited",
                "message": "Changes generated without ROM analysis - upload ROM file with XML definition for detailed changes",
                "recommendations": [
                    "Upload ROM file for detailed analysis",
                    "Provide XML definition file for accurate table mapping",
                    "Verify changes with dyno testing"
                ]
            },
            "safety_warnings": ["ROM analysis not available - changes are generic"],
            "rom_compatibility": {"status": "unknown", "message": "ROM file not analyzed"}
        }

    def _estimate_power_gain(self, changes: List[Dict]) -> str:
        """Estimate power gain from changes"""

        if not changes:
            return "0 HP"

        # Calculate impact score
        total_impact = 0
        for change in changes:
            priority_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(change.get("priority", "medium"), 2)
            cell_count = change.get("affected_cells", 0)
            max_change = change.get("safety_check", {}).get("max_change_percent", 0)

            impact = priority_weight * (cell_count / 10) * (max_change / 10)
            total_impact += impact

        # Map impact to power gain estimate
        if total_impact <= 5:
            return "+2-5 HP"
        elif total_impact <= 15:
            return "+5-10 HP"
        elif total_impact <= 30:
            return "+10-15 HP"
        elif total_impact <= 50:
            return "+15-25 HP"
        else:
            return "+25-35 HP"

    def _assess_safety_rating(self, changes: List[Dict]) -> str:
        """Assess overall safety rating of changes"""

        if not changes:
            return "Safe"

        critical_count = sum(1 for c in changes if c.get("priority") == "critical")
        max_change = max((c.get("safety_check", {}).get("max_change_percent", 0) for c in changes), default=0)
        warning_count = sum(len(c.get("safety_check", {}).get("warnings", [])) for c in changes)

        if critical_count > 3 or max_change > 20 or warning_count > 10:
            return "Aggressive"
        elif critical_count > 1 or max_change > 15 or warning_count > 5:
            return "Moderate"
        elif critical_count > 0 or max_change > 10 or warning_count > 2:
            return "Conservative"
        else:
            return "Safe"

    def _validate_changes(self, changes: List[Dict]) -> Dict[str, Any]:
        """Validate proposed changes comprehensively"""

        validation = {
            "status": "valid",
            "warnings": [],
            "recommendations": [],
            "statistics": {
                "total_changes": len(changes),
                "critical_changes": 0,
                "high_impact_changes": 0,
                "tables_affected": len(set(c.get("table_name", "") for c in changes))
            }
        }

        if not changes:
            validation["status"] = "no_changes"
            validation["warnings"].append("No changes generated")
            return validation

        # Count change types
        for change in changes:
            if change.get("priority") == "critical":
                validation["statistics"]["critical_changes"] += 1
            if change.get("safety_check", {}).get("max_change_percent", 0) > 10:
                validation["statistics"]["high_impact_changes"] += 1

        # Validation checks
        if validation["statistics"]["critical_changes"] > 5:
            validation["warnings"].append("Many critical changes detected")
            validation["recommendations"].append("Consider applying changes in stages")

        if validation["statistics"]["high_impact_changes"] > 8:
            validation["warnings"].append("Many high-impact changes detected")
            validation["recommendations"].append("Monitor engine parameters closely after changes")

        # Check for table conflicts
        table_changes = {}
        for change in changes:
            table_name = change.get("table_name", "")
            if table_name in table_changes:
                validation["warnings"].append(f"Multiple changes to table: {table_name}")
            table_changes[table_name] = change

        # Safety recommendations
        if any(c.get("priority") == "critical" for c in changes):
            validation["recommendations"].extend([
                "Perform dyno testing to validate changes",
                "Monitor AFR and knock sensors closely",
                "Have backup tune ready"
            ])

        return validation

    def _assess_rom_compatibility(self, rom_data: Dict) -> Dict[str, Any]:
        """Assess ROM compatibility and quality"""

        compatibility = {
            "status": "compatible",
            "confidence": "high",
            "issues": [],
            "recommendations": []
        }

        if not rom_data:
            compatibility["status"] = "unknown"
            compatibility["confidence"] = "none"
            compatibility["issues"].append("No ROM data available")
            return compatibility

        # Check table count
        table_count = rom_data.get("table_count", 0)
        if table_count < 50:
            compatibility["issues"].append("Low table count - definition may be incomplete")
            compatibility["confidence"] = "medium"
        elif table_count > 500:
            compatibility["recommendations"].append("High table count - verify definition accuracy")

        # Check for definition source
        if not rom_data.get("definition_source"):
            compatibility["issues"].append("No XML definition source specified")
            compatibility["confidence"] = "medium"

        # Check ROM integrity
        if "analysis_metadata" in rom_data:
            metadata = rom_data["analysis_metadata"]
            if not metadata.get("definition_used", False):
                compatibility["status"] = "limited"
                compatibility["issues"].append("ROM parsed without XML definition")

        return compatibility

    def _generate_change_summary(self, changes: List[Dict]) -> Dict[str, Any]:
        """Generate summary of all changes"""

        summary = {
            "by_priority": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_table_type": {},
            "total_cells_affected": 0,
            "avg_change_percent": 0,
            "max_change_percent": 0
        }

        if not changes:
            return summary

        all_changes = []

        for change in changes:
            # Count by priority
            priority = change.get("priority", "medium")
            summary["by_priority"][priority] += 1

            # Count by table type
            table_name = change.get("table_name", "Unknown")
            table_type = self._categorize_table(table_name)
            summary["by_table_type"][table_type] = summary["by_table_type"].get(table_type, 0) + 1

            # Accumulate statistics
            summary["total_cells_affected"] += change.get("affected_cells", 0)

            max_change = change.get("safety_check", {}).get("max_change_percent", 0)
            all_changes.append(max_change)

        if all_changes:
            summary["avg_change_percent"] = round(np.mean(all_changes), 2)
            summary["max_change_percent"] = round(max(all_changes), 2)

        return summary

    def _categorize_table(self, table_name: str) -> str:
        """Categorize table by type"""
        table_lower = table_name.lower()

        if any(keyword in table_lower for keyword in ["fuel", "injector", "pulse"]):
            return "Fuel"
        elif any(keyword in table_lower for keyword in ["timing", "ignition"]):
            return "Timing"
        elif any(keyword in table_lower for keyword in ["boost", "wastegate"]):
            return "Boost"
        elif any(keyword in table_lower for keyword in ["idle", "iac"]):
            return "Idle"
        elif any(keyword in table_lower for keyword in ["learning", "correction"]):
            return "Learning"
        else:
            return "Other"

# Example usage
if __name__ == "__main__":
    engine = TuningEngine()

    # This would be used with actual ROM and datalog data
    # changes = engine.generate_tune_changes(rom_data, datalog_analysis, suggestions)
    # print(f"Generated {changes['total_changes']} changes with safety rating: {changes['safety_rating']}")
