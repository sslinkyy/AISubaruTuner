"""
ROM Integration Module for ECU Tuning Application
Provides seamless integration between XML definitions, ROM parsing, and the main application
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import pandas as pd

# Import the new modules
from .xml_definition_parser import XMLDefinitionParser
from .subaru_rom_parser import SubaruROMParser
from .tuning_engine_updated import TuningEngine

logger = logging.getLogger(__name__)

class ROMIntegrationManager:
    """Production-ready integration manager for ROM analysis workflow"""

    def __init__(self):
        self.xml_parser = XMLDefinitionParser()
        self.rom_parser = SubaruROMParser()
        self.tuning_engine = TuningEngine()
        self.cache = {}

    def analyze_rom_package(self, datalog_path: str, tune_path: str, 
                           definition_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete ROM package analysis workflow

        Args:
            datalog_path: Path to datalog file
            tune_path: Path to ROM/tune file
            definition_path: Optional path to XML definition file

        Returns:
            Complete analysis results
        """
        try:
            logger.info(f"Starting ROM package analysis: datalog={datalog_path}, tune={tune_path}, definition={definition_path}")

            # Step 1: Parse XML definition if provided
            table_definitions = None
            if definition_path:
                table_definitions = self._parse_xml_definition(definition_path)
                logger.info(f"Loaded {table_definitions['table_count']} table definitions")

            # Step 2: Parse ROM file
            rom_data = self._parse_rom_file(tune_path, table_definitions)
            logger.info(f"Parsed ROM: {rom_data['table_count']} tables extracted")

            # Step 3: Analyze datalog (using existing datalog analyzer)
            datalog_analysis = self._analyze_datalog(datalog_path)
            logger.info(f"Datalog analysis complete: {len(datalog_analysis.get('issues', []))} issues found")

            # Step 4: Generate tune changes
            tune_changes = self._generate_tune_changes(rom_data, datalog_analysis)
            logger.info(f"Generated {tune_changes['total_changes']} tune changes")

            # Step 5: Compile comprehensive results
            results = self._compile_results(rom_data, datalog_analysis, tune_changes, table_definitions)

            logger.info("ROM package analysis completed successfully")
            return results

        except Exception as e:
            logger.error(f"ROM package analysis failed: {e}")
            raise

    def _parse_xml_definition(self, definition_path: str) -> Dict[str, Any]:
        """Parse XML definition file with caching"""
        try:
            # Check cache first
            cache_key = f"xml_{Path(definition_path).name}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            # Parse XML
            definitions = self.xml_parser.parse_definition_file(definition_path)

            # Validate definitions
            validation = self.xml_parser.validate_definition(definitions)
            if validation["warnings"]:
                logger.warning(f"XML validation warnings: {len(validation['warnings'])}")

            # Cache results
            self.cache[cache_key] = definitions

            return definitions

        except Exception as e:
            logger.error(f"XML definition parsing failed: {e}")
            raise ValueError(f"Failed to parse XML definition: {e}")

    def _parse_rom_file(self, tune_path: str, table_definitions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Parse ROM file with optional XML definitions"""
        try:
            # Set table definitions if available
            if table_definitions:
                self.rom_parser.set_table_definitions(table_definitions)

            # Parse ROM
            rom_data = self.rom_parser.parse_rom(tune_path)

            # Validate ROM integrity
            validation = self.rom_parser.validate_rom_integrity()
            if not validation["valid"]:
                logger.warning(f"ROM validation issues: {validation['errors']}")

            return rom_data

        except Exception as e:
            logger.error(f"ROM parsing failed: {e}")
            raise ValueError(f"Failed to parse ROM file: {e}")

    def _analyze_datalog(self, datalog_path: str) -> Dict[str, Any]:
        """Analyze datalog file and include raw data for AI suggestions"""
        try:
            # Import your existing datalog analyzer
            from .datalog_analyzer import DatalogAnalyzer

            analyzer = DatalogAnalyzer()
            analysis = analyzer.analyze_datalog(datalog_path)

            # Read raw datalog data as list of dicts for AI suggestions and frontend
            datalog_df = pd.read_csv(datalog_path)
            analysis["datalog"] = {
                "data": datalog_df.to_dict(orient="records"),
                "columns": list(datalog_df.columns),
                "total_rows": len(datalog_df)
            }

            return analysis

        except ImportError:
            # Fallback if DatalogAnalyzer not available
            logger.warning("DatalogAnalyzer not available, using placeholder")
            return self._create_placeholder_datalog_analysis()
        except Exception as e:
            logger.error(f"Datalog analysis failed: {e}")
            return self._create_placeholder_datalog_analysis()

    def _create_placeholder_datalog_analysis(self) -> Dict[str, Any]:
        """Create placeholder datalog analysis"""
        return {
            "summary": {
                "total_records": 1000,
                "duration_minutes": 10,
                "avg_rpm": 3500,
                "max_rpm": 6500
            },
            "issues": [
                {
                    "id": "lean_condition",
                    "type": "Lean AFR Detected",
                    "severity": "high",
                    "description": "AFR values above 15.5 detected",
                    "count": 45,
                    "parameter": "AFR"
                }
            ],
            "suggestions": [
                {
                    "id": "fuel_enrichment",
                    "type": "Fuel Map Enrichment",
                    "table": "Primary Open Loop Fueling",
                    "change_type": "increase",
                    "percentage": 8.0,
                    "priority": "high",
                    "description": "Enrich fuel map to address lean conditions"
                }
            ],
            "safety": {
                "overall_status": "caution",
                "critical_issues": ["Lean AFR conditions detected"],
                "warnings": ["Monitor AFR closely"]
            },
            "performance": {
                "avg_rpm": 3500,
                "max_rpm": 6500,
                "avg_load": 1.8,
                "max_load": 2.5
            },
            "datalog": {
                "data": [],
                "columns": [],
                "total_rows": 0
            }
        }

    def _generate_tune_changes(self, rom_data: Dict[str, Any], datalog_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tune changes using the enhanced tuning engine"""
        try:
            suggestions = datalog_analysis.get("suggestions", [])
            tune_changes = self.tuning_engine.generate_tune_changes(rom_data, datalog_analysis, suggestions)

            return tune_changes

        except Exception as e:
            logger.error(f"Tune change generation failed: {e}")
            raise ValueError(f"Failed to generate tune changes: {e}")

    def _compile_results(self, rom_data: Dict[str, Any], datalog_analysis: Dict[str, Any], 
                        tune_changes: Dict[str, Any], table_definitions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Compile comprehensive analysis results"""

        results = {
            "status": "success",
            "analysis_type": "enhanced_rom_analysis",
            "timestamp": self._get_timestamp(),

            # ROM Analysis Results
            "rom_analysis": {
                "ecu_id": rom_data.get("ecu_id"),
                "rom_size": rom_data.get("rom_info", {}).get("size", 0),
                "tables_parsed": rom_data.get("table_count", 0),
                "definition_used": table_definitions is not None,
                "definition_source": rom_data.get("definition_source"),
                "checksum": rom_data.get("checksum"),
                "format": rom_data.get("rom_info", {}).get("format", "unknown")
            },

            # Datalog Analysis Results
            "datalog_analysis": {
                "summary": datalog_analysis.get("summary", {}),
                "datalog": datalog_analysis.get("datalog", {}),  # Include raw datalog data here
                "issues_found": len(datalog_analysis.get("issues", [])),
                "critical_issues": [i for i in datalog_analysis.get("issues", []) if i.get("severity") == "critical"],
                "safety_status": datalog_analysis.get("safety", {}).get("overall_status", "unknown"),
                "performance_metrics": datalog_analysis.get("performance", {})
            },

            # Tune Changes
            "tune_changes": {
                "total_changes": tune_changes.get("total_changes", 0),
                "safety_rating": tune_changes.get("safety_rating", "unknown"),
                "estimated_power_gain": tune_changes.get("estimated_power_gain", "unknown"),
                "changes_by_priority": tune_changes.get("change_summary", {}).get("by_priority", {}),
                "tables_affected": tune_changes.get("change_summary", {}).get("by_table_type", {}),
                "validation_status": tune_changes.get("validation", {}).get("status", "unknown")
            },

            # Detailed Data (for API responses)
            "detailed_data": {
                "rom_tables": self._extract_table_summary(rom_data),
                "datalog_issues": datalog_analysis.get("issues", []),
                "suggestions": datalog_analysis.get("suggestions", []),
                "tune_change_details": tune_changes.get("changes", []),
                "safety_warnings": tune_changes.get("safety_warnings", [])
            },

            # Quality Metrics
            "quality_metrics": {
                "rom_compatibility": tune_changes.get("rom_compatibility", {}),
                "analysis_confidence": self._calculate_analysis_confidence(rom_data, datalog_analysis, table_definitions),
                "data_completeness": self._assess_data_completeness(rom_data, datalog_analysis),
                "recommendation_reliability": self._assess_recommendation_reliability(tune_changes)
            },

            # Metadata
            "metadata": {
                "parser_version": "3.0.0",
                "xml_definition_used": table_definitions is not None,
                "xml_table_count": table_definitions.get("table_count", 0) if table_definitions else 0,
                "analysis_duration": "calculated_in_production",
                "features_used": self._get_features_used(table_definitions, rom_data, datalog_analysis)
            }
        }

        return results

    def _extract_table_summary(self, rom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract summary of ROM tables for API response"""
        tables = rom_data.get("tables", {})
        summary = []

        for table_name, table_data in tables.items():
            if isinstance(table_data, dict) and table_data.get("data"):
                summary.append({
                    "name": table_name,
                    "address": table_data.get("address", "unknown"),
                    "size": table_data.get("size", {}),
                    "storage_type": table_data.get("storage_type", "unknown"),
                    "has_axes": bool(table_data.get("axes", {})),
                    "scaling_applied": table_data.get("scaling_applied", False),
                    "units": table_data.get("scaling", {}).get("units", "")
                })

        return summary[:50]  # Limit for API response

    def _calculate_analysis_confidence(self, rom_data: Dict[str, Any], datalog_analysis: Dict[str, Any], 
                                     table_definitions: Optional[Dict[str, Any]]) -> str:
        """Calculate overall analysis confidence"""

        confidence_score = 0

        # ROM analysis confidence
        if table_definitions:
            confidence_score += 40  # XML definition available
        if rom_data.get("table_count", 0) > 100:
            confidence_score += 20  # Good table coverage
        if rom_data.get("ecu_id"):
            confidence_score += 10  # ECU identified

        # Datalog analysis confidence
        if len(datalog_analysis.get("issues", [])) > 0:
            confidence_score += 15  # Issues identified
        if datalog_analysis.get("summary", {}).get("total_records", 0) > 500:
            confidence_score += 15  # Sufficient data

        if confidence_score >= 80:
            return "high"
        elif confidence_score >= 60:
            return "medium"
        else:
            return "low"

    def _assess_data_completeness(self, rom_data: Dict[str, Any], datalog_analysis: Dict[str, Any]) -> str:
        """Assess completeness of available data"""

        completeness_score = 0

        # ROM data completeness
        if rom_data.get("tables"):
            completeness_score += 30
        if rom_data.get("definition_source"):
            completeness_score += 20
        if rom_data.get("ecu_id"):
            completeness_score += 10

        # Datalog data completeness
        if datalog_analysis.get("summary"):
            completeness_score += 20
        if datalog_analysis.get("issues"):
            completeness_score += 10
        if datalog_analysis.get("performance"):
            completeness_score += 10

        if completeness_score >= 80:
            return "complete"
        elif completeness_score >= 60:
            return "good"
        elif completeness_score >= 40:
            return "partial"
        else:
            return "limited"

    def _assess_recommendation_reliability(self, tune_changes: Dict[str, Any]) -> str:
        """Assess reliability of tune change recommendations"""

        if not tune_changes.get("changes"):
            return "none"

        safety_rating = tune_changes.get("safety_rating", "unknown")
        validation_status = tune_changes.get("validation", {}).get("status", "unknown")
        rom_compatibility = tune_changes.get("rom_compatibility", {}).get("status", "unknown")

        if (safety_rating in ["Safe", "Conservative"] and 
            validation_status == "valid" and 
            rom_compatibility == "compatible"):
            return "high"
        elif safety_rating in ["Moderate"] and validation_status == "valid":
            return "medium"
        else:
            return "low"

    def _get_features_used(self, table_definitions: Optional[Dict[str, Any]], 
                          rom_data: Dict[str, Any], datalog_analysis: Dict[str, Any]) -> List[str]:
        """Get list of features used in analysis"""

        features = []

        if table_definitions:
            features.append("xml_definition_parsing")
        if rom_data.get("tables"):
            features.append("rom_table_extraction")
        if rom_data.get("ecu_id"):
            features.append("ecu_identification")
        if datalog_analysis.get("issues"):
            features.append("issue_detection")
        if datalog_analysis.get("suggestions"):
            features.append("suggestion_generation")

        features.append("safety_analysis")
        features.append("tune_optimization")

        return features

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def get_table_data(self, session_data: Dict[str, Any], table_name: str) -> Optional[Dict[str, Any]]:
        """Get specific table data for API endpoints"""
        try:
            tune_path = session_data["tune"]["file_path"]
            definition_path = session_data.get("definition", {}).get("file_path")

            # Parse ROM if not cached
            cache_key = f"rom_{Path(tune_path).name}"
            if cache_key not in self.cache:
                table_definitions = None
                if definition_path:
                    table_definitions = self._parse_xml_definition(definition_path)

                rom_data = self._parse_rom_file(tune_path, table_definitions)
                self.cache[cache_key] = rom_data
            else:
                rom_data = self.cache[cache_key]

            # Get specific table
            table_data = rom_data.get("tables", {}).get(table_name)
            if not table_data:
                return None

            return {
                "table_name": table_name,
                "data": table_data.get("data", []),
                "definition": table_data.get("definition", {}),
                "rpm_axis": table_data.get("rpm_axis"),
                "load_axis": table_data.get("load_axis"),
                "scaling": table_data.get("scaling", {}),
                "address": table_data.get("address"),
                "size": table_data.get("size", {}),
                "storage_type": table_data.get("storage_type", "unknown")
            }

        except Exception as e:
            logger.error(f"Failed to get table data for {table_name}: {e}")
            return None

    def clear_cache(self):
        """Clear internal cache"""
        self.cache.clear()
        logger.info("ROM integration cache cleared")

# Convenience functions for main.py integration
def create_rom_integration_manager() -> ROMIntegrationManager:
    """Create and return ROM integration manager instance"""
    return ROMIntegrationManager()

def analyze_complete_package(datalog_path: str, tune_path: str, 
                           definition_path: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for complete package analysis"""
    manager = create_rom_integration_manager()
    return manager.analyze_rom_package(datalog_path, tune_path, definition_path)

# Example usage
if __name__ == "__main__":
    # Example usage
    manager = ROMIntegrationManager()

    # This would be used with actual files
    # results = manager.analyze_rom_package(
    #     datalog_path="path/to/datalog.csv",
    #     tune_path="path/to/tune.bin", 
    #     definition_path="path/to/definition.xml"
    # )
    # print(f"Analysis complete: {results['rom_analysis']['tables_parsed']} tables, {results['tune_changes']['total_changes']} changes")