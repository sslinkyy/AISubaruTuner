import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class XMLDefinitionParser:
    """Production-ready XML definition parser for Subaru ROM definitions"""

    def __init__(self):
        self.cache = {}
        self.supported_versions = ["1.0", "1.1", "1.2"]

    def parse_definition_file(self, xml_path: str) -> Dict[str, Any]:
        """Parse XML definition file with caching and validation"""
        try:
            # Check cache first
            file_hash = self._get_file_hash(xml_path)
            if file_hash in self.cache:
                logger.info(f"Using cached XML definition for {xml_path}")
                return self.cache[file_hash]

            # Parse XML
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Validate XML structure
            self._validate_xml_structure(root)

            # Parse definition
            definition = self._parse_xml_root(root)

            # Add metadata
            definition["metadata"] = {
                "source_file": xml_path,
                "file_hash": file_hash,
                "parsed_at": self._get_timestamp(),
                "parser_version": "3.0.0"
            }

            # Cache result
            self.cache[file_hash] = definition

            logger.info(f"Parsed XML definition: {len(definition['tables'])} tables, {len(definition['roms'])} ROM(s)")
            return definition

        except ET.ParseError as e:
            logger.error(f"XML parsing error in {xml_path}: {e}")
            raise ValueError(f"Invalid XML format: {e}")
        except Exception as e:
            logger.error(f"Failed to parse XML definition {xml_path}: {e}")
            raise

    def _validate_xml_structure(self, root: ET.Element):
        """Validate XML structure and version"""
        if root.tag != "roms":
            raise ValueError("XML root element must be 'roms'")

        # Check for at least one ROM definition
        roms = root.findall("rom")
        if not roms:
            raise ValueError("No ROM definitions found in XML")

        # Validate each ROM has required attributes
        for rom in roms:
            if not rom.get("id") and not rom.get("name"):
                raise ValueError("ROM definition missing id or name attribute")

    def _parse_xml_root(self, root: ET.Element) -> Dict[str, Any]:
        """Parse the root XML element"""
        definition = {
            "roms": {},
            "tables": {},
            "table_count": 0,
            "rom_count": 0
        }

        for rom_elem in root.findall("rom"):
            rom_data = self._parse_rom_element(rom_elem)
            rom_id = rom_data["id"]
            definition["roms"][rom_id] = rom_data

            # Add tables to global table dictionary with ROM context
            for table_name, table_data in rom_data["tables"].items():
                table_key = f"{rom_id}:{table_name}"
                definition["tables"][table_key] = table_data
                definition["tables"][table_name] = table_data  # Also add without ROM prefix for compatibility

        definition["table_count"] = len(definition["tables"])
        definition["rom_count"] = len(definition["roms"])

        return definition

    def _parse_rom_element(self, rom_elem: ET.Element) -> Dict[str, Any]:
        """Parse a single ROM element"""
        rom_data = {
            "id": rom_elem.get("id", rom_elem.get("name", "unknown")),
            "name": rom_elem.get("name", ""),
            "base": rom_elem.get("base", ""),
            "memmodel": rom_elem.get("memmodel", ""),
            "flashmethod": rom_elem.get("flashmethod", ""),
            "checksummodule": rom_elem.get("checksummodule", ""),
            "tables": {},
            "table_count": 0
        }

        # Parse all table elements
        for table_elem in rom_elem.findall(".//table[@name]"):
            table_data = self._parse_table_element(table_elem)
            if table_data:
                rom_data["tables"][table_data["name"]] = table_data

        rom_data["table_count"] = len(rom_data["tables"])
        return rom_data

    def _parse_table_element(self, table_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a single table element"""
        try:
            table_data = {
                "name": table_elem.get("name", ""),
                "storageaddress": table_elem.get("storageaddress", ""),
                "sizex": int(table_elem.get("sizex", "16")),
                "sizey": int(table_elem.get("sizey", "16")),
                "storagetype": table_elem.get("storagetype", "uint8"),
                "endian": table_elem.get("endian", "big"),
                "type": table_elem.get("type", "3D"),
                "children": [],
                "states": [],
                "scaling": self._parse_scaling(table_elem),
                "description": table_elem.get("description", "")
            }

            # Parse child tables (axes, etc.)
            for child_table in table_elem.findall("table"):
                child_data = self._parse_table_element(child_table)
                if child_data:
                    table_data["children"].append(child_data)

            # Parse states
            for state_elem in table_elem.findall("state"):
                state_data = {
                    "name": state_elem.get("name", ""),
                    "data": state_elem.get("data", "")
                }
                table_data["states"].append(state_data)

            # Validate required fields
            if not table_data["name"]:
                logger.warning("Table missing name attribute, skipping")
                return None

            if not table_data["storageaddress"]:
                logger.warning(f"Table {table_data['name']} missing storageaddress, skipping")
                return None

            # Validate storage address format
            try:
                int(table_data["storageaddress"], 16)
            except ValueError:
                logger.warning(f"Table {table_data['name']} has invalid storageaddress format")
                return None

            return table_data

        except Exception as e:
            logger.error(f"Error parsing table element: {e}")
            return None

    def _parse_scaling(self, table_elem: ET.Element) -> Dict[str, Any]:
        """Parse scaling information from table element"""
        scaling = {
            "units": "",
            "to_byte": "x",
            "to_real": "x",
            "format": "%.2f",
            "min": 0,
            "max": 255,
            "inc": 1
        }

        # Look for scaling attributes directly on table
        for attr in ["units", "to_byte", "to_real", "format"]:
            if table_elem.get(attr):
                scaling[attr] = table_elem.get(attr)

        return scaling

    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file caching"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return str(hash(file_path))

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def get_table_by_name(self, definition: Dict[str, Any], table_name: str) -> Optional[Dict[str, Any]]:
        """Get table definition by name"""
        return definition["tables"].get(table_name)

    def get_table_by_address(self, definition: Dict[str, Any], address: str) -> Optional[Dict[str, Any]]:
        """Get table definition by storage address"""
        address_lower = address.lower()
        for table in definition["tables"].values():
            if table["storageaddress"].lower() == address_lower:
                return table
        return None

    def get_tables_by_type(self, definition: Dict[str, Any], table_type: str) -> List[Dict[str, Any]]:
        """Get all tables of a specific type"""
        return [table for table in definition["tables"].values() if table["type"] == table_type]

    def validate_definition(self, definition: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parsed definition for completeness"""
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "stats": {
                "total_tables": len(definition["tables"]),
                "tables_with_addresses": 0,
                "tables_with_scaling": 0,
                "duplicate_addresses": []
            }
        }

        addresses_seen = {}

        for table_name, table in definition["tables"].items():
            # Check for storage address
            if table["storageaddress"]:
                validation["stats"]["tables_with_addresses"] += 1

                # Check for duplicate addresses
                addr = table["storageaddress"].lower()
                if addr in addresses_seen:
                    validation["stats"]["duplicate_addresses"].append({
                        "address": addr,
                        "tables": [addresses_seen[addr], table_name]
                    })
                    validation["warnings"].append(f"Duplicate address {addr} in tables {addresses_seen[addr]} and {table_name}")
                else:
                    addresses_seen[addr] = table_name
            else:
                validation["warnings"].append(f"Table {table_name} missing storage address")

            # Check for scaling info
            if table["scaling"]["units"] or table["scaling"]["to_real"] != "x":
                validation["stats"]["tables_with_scaling"] += 1

        if validation["warnings"]:
            logger.warning(f"XML validation warnings: {len(validation['warnings'])} issues found")

        return validation

# Example usage and testing
if __name__ == "__main__":
    parser = XMLDefinitionParser()

    # This would be used with your actual XML file
    # definition = parser.parse_definition_file("path/to/definition.xml")
    # validation = parser.validate_definition(definition)
    # print(f"Loaded {definition['table_count']} tables from {definition['rom_count']} ROMs")
