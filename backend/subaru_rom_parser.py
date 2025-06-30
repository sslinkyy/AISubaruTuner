import logging
import struct
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class SubaruROMParser:
    """Production-ready Subaru ROM parser with XML definition support"""

    def __init__(self):
        self.table_definitions = None
        self.rom_data = None
        self.rom_size = 0
        self.supported_storage_types = {
            'uint8': {'size': 1, 'format': 'B', 'signed': False},
            'int8': {'size': 1, 'format': 'b', 'signed': True},
            'uint16': {'size': 2, 'format': 'H', 'signed': False},
            'int16': {'size': 2, 'format': 'h', 'signed': True},
            'uint32': {'size': 4, 'format': 'I', 'signed': False},
            'int32': {'size': 4, 'format': 'i', 'signed': True},
            'float': {'size': 4, 'format': 'f', 'signed': True}
        }

    def set_table_definitions(self, definitions: Dict[str, Any]):
        """Set XML table definitions for ROM parsing"""
        self.table_definitions = definitions
        logger.info(f"Loaded {definitions['table_count']} table definitions")

    def parse_rom(self, rom_path: str) -> Dict[str, Any]:
        """Parse ROM file using XML definitions"""
        try:
            # Load ROM file
            with open(rom_path, 'rb') as f:
                self.rom_data = f.read()

            self.rom_size = len(self.rom_data)
            logger.info(f"Loaded ROM file: {rom_path} ({self.rom_size} bytes)")

            # Generate ROM metadata
            rom_info = self._generate_rom_metadata(rom_path)

            # Parse tables if definitions available
            tables = {}
            if self.table_definitions:
                tables = self._parse_all_tables()
            else:
                logger.warning("No table definitions available - performing basic ROM analysis only")
                tables = self._perform_basic_analysis()

            result = {
                "rom_info": rom_info,
                "tables": tables,
                "table_count": len(tables),
                "definition_source": self.table_definitions["metadata"]["source_file"] if self.table_definitions else None,
                "ecu_id": self._detect_ecu_id(),
                "checksum": self._calculate_checksum(),
                "analysis_metadata": {
                    "parsed_at": self._get_timestamp(),
                    "parser_version": "3.0.0",
                    "rom_size": self.rom_size,
                    "tables_parsed": len(tables),
                    "definition_used": self.table_definitions is not None
                }
            }

            logger.info(f"ROM parsing complete: {len(tables)} tables extracted")
            return result

        except Exception as e:
            logger.error(f"ROM parsing failed: {e}")
            raise

    def _generate_rom_metadata(self, rom_path: str) -> Dict[str, Any]:
        """Generate ROM metadata"""
        return {
            "filename": Path(rom_path).name,
            "size": self.rom_size,
            "hash": hashlib.md5(self.rom_data).hexdigest(),
            "format": self._detect_rom_format(),
            "endianness": self._detect_endianness(),
            "created_at": self._get_timestamp()
        }

    def _parse_all_tables(self) -> Dict[str, Any]:
        """Parse all tables using XML definitions"""
        tables = {}

        if not self.table_definitions:
            return tables

        # Parse main tables
        for table_name, table_def in self.table_definitions["tables"].items():
            if ":" in table_name:  # Skip ROM-prefixed duplicates
                continue

            try:
                table_data = self._parse_single_table(table_def)
                if table_data:
                    tables[table_name] = table_data
            except Exception as e:
                logger.error(f"Failed to parse table {table_name}: {e}")
                # Add placeholder for failed table
                tables[table_name] = {
                    "name": table_name,
                    "data": None,
                    "error": str(e),
                    "definition": table_def
                }

        return tables

    def _parse_single_table(self, table_def: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single table from ROM"""
        try:
            # Support both 'storageaddress' and 'address' keys
            address_str = table_def.get("storageaddress") or table_def.get("address")
            if not address_str:
                logger.warning(f"Table {table_def.get('name')} missing address attribute")
                return None
            address = int(address_str, 16)
            sizex = table_def["sizex"]
            sizey = table_def["sizey"]
            storage_type = table_def["storagetype"]
            endian = table_def["endian"]

            # Validate address bounds
            if not self._validate_address_bounds(address, sizex, sizey, storage_type):
                logger.warning(f"Table {table_def['name']} address out of bounds: {hex(address)}")
                return None

            # Extract table data
            raw_data = self._extract_table_data(address, sizex, sizey, storage_type, endian)

            # Apply scaling if available
            scaled_data = self._apply_scaling(raw_data, table_def.get("scaling", {}))

            # Parse axes if available
            axes = self._parse_table_axes(table_def)

            return {
                "name": table_def["name"],
                "data": scaled_data,
                "raw_data": raw_data,
                "definition": table_def,
                "address": address,
                "size": {"x": sizex, "y": sizey},
                "storage_type": storage_type,
                "axes": axes,
                "rpm_axis": axes.get("rpm_axis"),
                "load_axis": axes.get("load_axis"),
                "scaling": table_def.get("scaling"),
                "checksum": self._calculate_table_checksum(raw_data),
                "extracted_at": self._get_timestamp()
            }

        except Exception as e:
            logger.error(f"Error parsing table {table_def.get('name', 'unknown')}: {e}")
            return None

    def _extract_table_data(self, address: int, sizex: int, sizey: int, 
                           storage_type: str, endian: str) -> List[List[float]]:
        """Extract raw table data from ROM"""
        if storage_type not in self.supported_storage_types:
            raise ValueError(f"Unsupported storage type: {storage_type}")

        type_info = self.supported_storage_types[storage_type]
        element_size = type_info["size"]
        format_char = type_info["format"]

        # Determine endianness
        endian_char = '>' if endian == 'big' else '<'
        format_string = f"{endian_char}{format_char}"

        data = []

        # For 1D tables (axes)
        if sizey == 1:
            row = []
            for x in range(sizex):
                offset = address + (x * element_size)
                if offset + element_size <= self.rom_size:
                    raw_bytes = self.rom_data[offset:offset + element_size]
                    value = struct.unpack(format_string, raw_bytes)[0]
                    row.append(float(value))
                else:
                    row.append(0.0)  # Default for out-of-bounds
            data.append(row)
        else:
            # For 2D tables
            for y in range(sizey):
                row = []
                for x in range(sizex):
                    offset = address + (y * sizex + x) * element_size
                    if offset + element_size <= self.rom_size:
                        raw_bytes = self.rom_data[offset:offset + element_size]
                        value = struct.unpack(format_string, raw_bytes)[0]
                        row.append(float(value))
                    else:
                        row.append(0.0)  # Default for out-of-bounds
                data.append(row)

        return data

    def _apply_scaling(self, raw_data: List[List[float]], scaling: Dict[str, Any]) -> List[List[float]]:
        """Apply scaling transformation to raw data"""
        if not scaling or scaling.get("to_real", "x") == "x":
            return raw_data

        try:
            scaled_data = []
            for row in raw_data:
                scaled_row = []
                for value in row:
                    # Apply scaling formula
                    if scaling["to_real"] == "x":
                        scaled_value = value
                    else:
                        # Replace 'x' with actual value in formula
                        formula = scaling["to_real"].replace('x', str(value))
                        try:
                            scaled_value = eval(formula)  # Note: In production, use safer evaluation
                        except:
                            scaled_value = value

                    scaled_row.append(float(scaled_value))
                scaled_data.append(scaled_row)

            return scaled_data

        except Exception as e:
            logger.warning(f"Scaling failed: {e}, returning raw data")
            return raw_data

    def _parse_table_axes(self, table_def: Dict[str, Any]) -> Dict[str, Any]:
        """Parse table axes from child table definitions"""
        axes = {}

        for child in table_def.get("children", []):
            axis_type = child.get("type", "").lower()
            child_name = child.get("name", "").lower()

            if "x axis" in axis_type or "rpm" in child_name:
                axis_data = self._parse_single_table(child)
                if axis_data and axis_data["data"]:
                    axes["rpm_axis"] = axis_data["data"][0]  # First row for 1D axis
                    axes["x_axis"] = axis_data

            elif "y axis" in axis_type or "load" in child_name or "map" in child_name:
                axis_data = self._parse_single_table(child)
                if axis_data and axis_data["data"]:
                    axes["load_axis"] = axis_data["data"][0]  # First row for 1D axis
                    axes["y_axis"] = axis_data

        return axes

    def _validate_address_bounds(self, address: int, sizex: int, sizey: int, storage_type: str) -> bool:
        """Validate that table address and size are within ROM bounds"""
        if storage_type not in self.supported_storage_types:
            return False

        element_size = self.supported_storage_types[storage_type]["size"]
        total_elements = sizex * sizey
        total_bytes = total_elements * element_size

        return address + total_bytes <= self.rom_size

    def _perform_basic_analysis(self) -> Dict[str, Any]:
        """Perform basic ROM analysis without XML definitions"""
        logger.info("Performing basic ROM analysis without XML definitions")

        # Look for common patterns and signatures
        analysis = {
            "basic_info": {
                "size": self.rom_size,
                "format": self._detect_rom_format(),
                "potential_tables": self._find_potential_tables(),
                "ascii_strings": self._extract_ascii_strings(),
                "checksum_locations": self._find_checksum_locations()
            }
        }

        return analysis

    def _find_potential_tables(self) -> List[Dict[str, Any]]:
        """Find potential table locations using pattern analysis"""
        potential_tables = []

        # Look for repeating patterns that might indicate tables
        # This is a simplified heuristic approach
        for i in range(0, self.rom_size - 256, 256):
            chunk = self.rom_data[i:i+256]

            # Check for patterns that might indicate table data
            if self._looks_like_table_data(chunk):
                potential_tables.append({
                    "address": hex(i),
                    "size_estimate": 256,
                    "confidence": "low",
                    "pattern_type": "repeating_values"
                })

        return potential_tables[:20]  # Limit to first 20 potential tables

    def _looks_like_table_data(self, data: bytes) -> bool:
        """Heuristic to determine if data looks like table data"""
        if len(data) < 16:
            return False

        # Check for reasonable value ranges (not all zeros or all 0xFF)
        unique_values = len(set(data))
        if unique_values < 3 or unique_values == 1:
            return False

        # Check for gradual changes (typical in tuning tables)
        changes = sum(1 for i in range(1, len(data)) if abs(data[i] - data[i-1]) <= 10)
        change_ratio = changes / (len(data) - 1)

        return change_ratio > 0.3  # At least 30% gradual changes

    def _extract_ascii_strings(self) -> List[str]:
        """Extract ASCII strings from ROM (might contain ECU info)"""
        strings = []
        current_string = ""

        for byte in self.rom_data:
            if 32 <= byte <= 126:  # Printable ASCII
                current_string += chr(byte)
            else:
                if len(current_string) >= 4:  # Minimum string length
                    strings.append(current_string)
                current_string = ""

        # Add final string if exists
        if len(current_string) >= 4:
            strings.append(current_string)

        return strings[:50]  # Limit to first 50 strings

    def _find_checksum_locations(self) -> List[Dict[str, Any]]:
        """Find potential checksum locations"""
        checksums = []

        # Common checksum locations in Subaru ROMs
        common_locations = [0x7FFC, 0xFFFC, 0x1FFFC, 0x3FFFC]

        for location in common_locations:
            if location < self.rom_size - 4:
                checksum_bytes = self.rom_data[location:location+4]
                checksum_value = struct.unpack('>I', checksum_bytes)[0]
                checksums.append({
                    "address": hex(location),
                    "value": hex(checksum_value),
                    "type": "potential_checksum"
                })

        return checksums

    def _detect_ecu_id(self) -> Optional[str]:
        """Attempt to detect ECU ID from ROM"""
        # Look for common ECU ID patterns in Subaru ROMs
        ecu_patterns = [
            b'22611A',  # Common Subaru ECU prefix
            b'22644A',
            b'22667A'
        ]

        for pattern in ecu_patterns:
            if pattern in self.rom_data:
                # Extract surrounding context
                index = self.rom_data.find(pattern)
                context = self.rom_data[max(0, index-10):index+20]
                try:
                    return context.decode('ascii', errors='ignore').strip()
                except:
                    pass

        return None

    def _detect_rom_format(self) -> str:
        """Detect ROM format based on size and patterns"""
        if self.rom_size == 1024 * 1024:  # 1MB
            return "Subaru_1MB"
        elif self.rom_size == 512 * 1024:  # 512KB
            return "Subaru_512KB"
        elif self.rom_size == 256 * 1024:  # 256KB
            return "Subaru_256KB"
        else:
            return f"Unknown_{self.rom_size}_bytes"

    def _detect_endianness(self) -> str:
        """Detect ROM endianness"""
        # Subaru ROMs are typically big-endian
        return "big"

    def _calculate_checksum(self) -> str:
        """Calculate ROM checksum"""
        return hashlib.md5(self.rom_data).hexdigest()

    def _calculate_table_checksum(self, data: List[List[float]]) -> str:
        """Calculate checksum for table data"""
        flat_data = [item for sublist in data for item in sublist]
        data_str = ','.join(map(str, flat_data))
        return hashlib.md5(data_str.encode()).hexdigest()[:8]

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def get_table_by_name(self, rom_data: Dict[str, Any], table_name: str) -> Optional[Dict[str, Any]]:
        """Get table data by name"""
        return rom_data.get("tables", {}).get(table_name)

    def get_table_data_at_address(self, address: str, sizex: int = 16, sizey: int = 16, 
                                 storage_type: str = "uint8") -> Optional[List[List[float]]]:
        """Extract table data at specific address"""
        if not self.rom_data:
            return None

        try:
            addr = int(address, 16)
            return self._extract_table_data(addr, sizex, sizey, storage_type, "big")
        except Exception as e:
            logger.error(f"Failed to extract data at address {address}: {e}")
            return None

    def validate_rom_integrity(self) -> Dict[str, Any]:
        """Validate ROM integrity and structure"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {
                "size": self.rom_size,
                "checksum": self._calculate_checksum(),
                "tables_parsed": 0,
                "tables_failed": 0
            }
        }

        # Basic size validation
        if self.rom_size < 64 * 1024:  # Minimum 64KB
            validation["errors"].append("ROM file too small")
            validation["valid"] = False

        if self.rom_size > 2 * 1024 * 1024:  # Maximum 2MB
            validation["warnings"].append("ROM file unusually large")

        # Check for common corruption patterns
        zero_blocks = self.rom_data.count(b'\x00' * 1024)
        if zero_blocks > 10:
            validation["warnings"].append(f"Found {zero_blocks} blocks of zeros - possible corruption")

        return validation

# Example usage
if __name__ == "__main__":
    parser = SubaruROMParser()

    # This would be used with your actual ROM file
    # rom_data = parser.parse_rom("path/to/rom.bin")
    # validation = parser.validate_rom_integrity()
    # print(f"Parsed {rom_data['table_count']} tables from ROM")