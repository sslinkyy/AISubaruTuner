import xml.etree.ElementTree as ET
import struct
import hashlib
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class XMLDefinitionParser:
    """Parser for RomRaider/Carberry XML definition files"""

    def __init__(self):
        self.tables = {}
        self.scaling_definitions = {}
        self.axes_definitions = {}

    def parse_definition_file(self, xml_path: str) -> Dict[str, Any]:
        """Parse XML definition file and extract table definitions"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            logger.info(f"Parsing XML definition: {xml_path}")

            # Parse scaling definitions first
            self._parse_scaling_definitions(root)

            # Parse table definitions
            tables = self._parse_table_definitions(root)

            logger.info(f"Parsed {len(tables)} table definitions from XML")

            return {
                "tables": tables,
                "scaling": self.scaling_definitions,
                "metadata": {
                    "source_file": xml_path,
                    "ecu_id": self._extract_ecu_id(root),
                    "version": root.get("version", "unknown")
                }
            }

        except Exception as e:
            logger.error(f"Error parsing XML definition: {e}")
            raise

    def _parse_scaling_definitions(self, root: ET.Element):
        """Parse scaling definitions from XML"""
        for scaling in root.findall('.//scaling'):
            name = scaling.get('name')
            if name:
                self.scaling_definitions[name] = {
                    'units': scaling.get('units', ''),
                    'to_byte': scaling.get('to_byte', ''),
                    'expression': scaling.get('expression', ''),
                    'format': scaling.get('format', '%.2f'),
                    'min': float(scaling.get('min', 0)),
                    'max': float(scaling.get('max', 1000)),
                    'inc': float(scaling.get('inc', 1))
                }

    def _parse_table_definitions(self, root: ET.Element) -> Dict[str, Any]:
        """Parse table definitions from XML"""
        tables = {}

        # Parse 3D tables (maps)
        for table in root.findall('.//table[@type="3D"]'):
            table_def = self._parse_3d_table(table)
            if table_def:
                tables[table_def['name']] = table_def

        # Parse 2D tables (curves)
        for table in root.findall('.//table[@type="2D"]'):
            table_def = self._parse_2d_table(table)
            if table_def:
                tables[table_def['name']] = table_def

        # Parse 1D tables (single values)
        for table in root.findall('.//table[@type="1D"]'):
            table_def = self._parse_1d_table(table)
            if table_def:
                tables[table_def['name']] = table_def

        return tables

    def _parse_3d_table(self, table: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse 3D table definition"""
        try:
            name = table.get('name')
            if not name:
                return None

            # Get table data element
            table_data = table.find('table')
            if table_data is None:
                return None

            address = int(table_data.get('address', '0'), 16)

            # Parse axes
            x_axis = self._parse_axis(table.find('.//table[@name="X"]'))
            y_axis = self._parse_axis(table.find('.//table[@name="Y"]'))

            if not x_axis or not y_axis:
                logger.warning(f"Missing axes for table {name}")
                return None

            # Get scaling
            scaling_name = table_data.get('scaling')
            scaling = self.scaling_definitions.get(scaling_name, {})

            return {
                'name': name,
                'type': '3D',
                'address': address,
                'rows': len(y_axis['values']),
                'cols': len(x_axis['values']),
                'data_type': table_data.get('type', 'uint8'),
                'endian': table_data.get('endian', 'big'),
                'scaling': scaling,
                'x_axis': x_axis,
                'y_axis': y_axis,
                'description': table.get('description', ''),
                'category': table.get('category', 'Unknown')
            }

        except Exception as e:
            logger.error(f"Error parsing 3D table: {e}")
            return None

    def _parse_2d_table(self, table: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse 2D table definition"""
        try:
            name = table.get('name')
            if not name:
                return None

            table_data = table.find('table')
            if table_data is None:
                return None

            address = int(table_data.get('address', '0'), 16)

            # Parse single axis
            x_axis = self._parse_axis(table.find('.//table[@name="X"]'))
            if not x_axis:
                return None

            scaling_name = table_data.get('scaling')
            scaling = self.scaling_definitions.get(scaling_name, {})

            return {
                'name': name,
                'type': '2D',
                'address': address,
                'rows': 1,
                'cols': len(x_axis['values']),
                'data_type': table_data.get('type', 'uint8'),
                'endian': table_data.get('endian', 'big'),
                'scaling': scaling,
                'x_axis': x_axis,
                'description': table.get('description', ''),
                'category': table.get('category', 'Unknown')
            }

        except Exception as e:
            logger.error(f"Error parsing 2D table: {e}")
            return None

    def _parse_1d_table(self, table: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse 1D table definition"""
        try:
            name = table.get('name')
            if not name:
                return None

            table_data = table.find('table')
            if table_data is None:
                return None

            address = int(table_data.get('address', '0'), 16)

            scaling_name = table_data.get('scaling')
            scaling = self.scaling_definitions.get(scaling_name, {})

            return {
                'name': name,
                'type': '1D',
                'address': address,
                'rows': 1,
                'cols': 1,
                'data_type': table_data.get('type', 'uint8'),
                'endian': table_data.get('endian', 'big'),
                'scaling': scaling,
                'description': table.get('description', ''),
                'category': table.get('category', 'Unknown')
            }

        except Exception as e:
            logger.error(f"Error parsing 1D table: {e}")
            return None

    def _parse_axis(self, axis_element: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse axis definition"""
        if axis_element is None:
            return None

        try:
            table_data = axis_element.find('table')
            if table_data is None:
                return None

            address = int(table_data.get('address', '0'), 16)
            length = int(table_data.get('length', '0'))

            scaling_name = table_data.get('scaling')
            scaling = self.scaling_definitions.get(scaling_name, {})

            # Generate default values if no specific values provided
            values = list(range(length))

            return {
                'address': address,
                'length': length,
                'data_type': table_data.get('type', 'uint8'),
                'endian': table_data.get('endian', 'big'),
                'scaling': scaling,
                'values': values
            }

        except Exception as e:
            logger.error(f"Error parsing axis: {e}")
            return None

    def _extract_ecu_id(self, root: ET.Element) -> str:
        """Extract ECU ID from XML"""
        ecu_id = root.get('ecuid')
        if ecu_id:
            return ecu_id
        rom_element = root.find('.//rom')
        if rom_element is not None:
            return rom_element.get('base', 'Unknown')
        return 'Unknown'

class SubaruROMParser:
    """Enhanced Subaru ROM parser with XML definition support"""

    def __init__(self):
        self.table_definitions = None
        self.default_definitions = self._get_default_definitions()

    def set_table_definitions(self, definitions: Dict[str, Any]):
        """Set table definitions from XML parser"""
        self.table_definitions = definitions

    def _get_default_definitions(self) -> Dict[str, Any]:
        """Fallback table definitions if no XML provided"""
        return {
            "tables": {
                "Primary_Open_Loop_Fueling": {
                    "name": "Primary Open Loop Fueling",
                    "type": "3D",
                    "address": 0x8000,
                    "rows": 16,
                    "cols": 16,
                    "data_type": "uint16",
                    "scaling": {"expression": "x*0.01", "units": "ms"},
                    "x_axis": {"values": list(range(16))},
                    "y_axis": {"values": list(range(16))},
                    "description": "Primary fuel injection pulse width"
                },
                "Ignition_Timing_Base": {
                    "name": "Ignition Timing Base",
                    "type": "3D",
                    "address": 0xA000,
                    "rows": 16,
                    "cols": 16,
                    "data_type": "uint8",
                    "scaling": {"expression": "x*0.5", "units": "degrees"},
                    "x_axis": {"values": list(range(16))},
                    "y_axis": {"values": list(range(16))},
                    "description": "Base ignition timing advance"
                }
            }
        }

    def parse_rom(self, rom_path: str) -> Dict[str, Any]:
        """Parse Subaru ROM file using XML definitions"""
        try:
            with open(rom_path, 'rb') as f:
                rom_data = f.read()

            logger.info(f"Parsing ROM file: {rom_path}, size: {len(rom_data)} bytes")

            # Use XML definitions if available, otherwise use defaults
            definitions = self.table_definitions or self.default_definitions

            tables = {}
            for table_name, definition in definitions["tables"].items():
                try:
                    table_data = self._extract_table_data(rom_data, definition)
                    tables[table_name] = {
                        "data": table_data,
                        "definition": definition,
                        "rpm_axis": self._get_axis_values(definition.get("y_axis")),
                        "load_axis": self._get_axis_values(definition.get("x_axis"))
                    }
                except Exception as e:
                    logger.warning(f"Failed to extract table {table_name}: {e}")
                    continue

            return {
                "rom_size": len(rom_data),
                "checksum": hashlib.md5(rom_data).hexdigest(),
                "tables": tables,
                "platform": "Subaru",
                "ecu_id": self._get_ecu_id(rom_data, definitions),
                "definition_source": "XML" if self.table_definitions else "Default"
            }

        except Exception as e:
            logger.error(f"Error parsing ROM: {e}")
            raise

    def _extract_table_data(self, rom_data: bytes, definition: Dict) -> List[List[float]]:
        """Extract table data from ROM using definition"""
        address = definition["address"]
        rows = definition["rows"]
        cols = definition["cols"]
        data_type = definition["data_type"]
        endian = definition.get("endian", "big")
        scaling = definition.get("scaling", {})

        if address >= len(rom_data):
            logger.warning(f"Table address {hex(address)} beyond ROM size")
            return [[0.0 for _ in range(cols)] for _ in range(rows)]

        # Determine data size
        if data_type == "uint16":
            data_size = 2
            format_char = 'H'
        elif data_type == "int16":
            data_size = 2
            format_char = 'h'
        elif data_type == "uint32":
            data_size = 4
            format_char = 'I'
        else:  # uint8 or int8
            data_size = 1
            format_char = 'B' if data_type == "uint8" else 'b'

        # Set endianness
        endian_char = '>' if endian == "big" else '<'

        table_data = []
        for row in range(rows):
            row_data = []
            for col in range(cols):
                offset = address + (row * cols + col) * data_size

                if offset + data_size <= len(rom_data):
                    raw_bytes = rom_data[offset:offset + data_size]
                    raw_value = struct.unpack(f'{endian_char}{format_char}', raw_bytes)[0]

                    # Apply scaling
                    scaled_value = self._apply_scaling(raw_value, scaling)
                    row_data.append(scaled_value)
                else:
                    row_data.append(0.0)

            table_data.append(row_data)

        return table_data

    def _apply_scaling(self, raw_value: int, scaling: Dict) -> float:
        """Apply scaling to raw value"""
        if not scaling:
            return float(raw_value)

        expression = scaling.get("expression", "x")

        # Simple expression evaluation (extend as needed)
        if "*" in expression:
            parts = expression.split("*")
            if len(parts) == 2 and parts[0].strip() == "x":
                multiplier = float(parts[1].strip())
                return raw_value * multiplier
        elif "+" in expression:
            parts = expression.split("+")
            if len(parts) == 2 and parts[0].strip() == "x":
                offset = float(parts[1].strip())
                return raw_value + offset
        elif "-" in expression:
            parts = expression.split("-")
            if len(parts) == 2 and parts[0].strip() == "x":
                offset = float(parts[1].strip())
                return raw_value - offset

        # Default: return raw value
        return float(raw_value)

    def _get_axis_values(self, axis_def: Optional[Dict]) -> Optional[List[float]]:
        """Get axis values from definition"""
        if not axis_def or "values" not in axis_def:
            return None

        return [float(v) for v in axis_def["values"]]

    def _get_ecu_id(self, rom_data: bytes, definitions: Dict) -> str:
        """Extract ECU ID from ROM or definitions"""
        if self.table_definitions:
            return definitions.get("metadata", {}).get("ecu_id", "Unknown")
        return "Subaru_Generic"