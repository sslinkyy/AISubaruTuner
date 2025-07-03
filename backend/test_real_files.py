import pytest
from pathlib import Path

from .rom_integration import ROMIntegrationManager


@pytest.fixture(scope="session")
@pytest.fixture(scope="session")
def sample_paths() -> Dict[str, str]:
    base = Path(__file__).resolve().parents[1] / "test_files"
    return {
        "datalog": str(base / "romraiderlog_4_20250616_162401.csv"),
        "rom": str(base / "test 192kb 4 Golden MAF Rom 2 EJ205-91OCT-EBCS-CATLESS-StockIntake.bin"),
        "definition": str(base / "Carberry 4.2_Imperial.xml"),
    }


def test_rom_package_analysis(sample_paths):
    manager = ROMIntegrationManager()
    result = manager.analyze_rom_package(
        datalog_path=sample_paths["datalog"],
        tune_path=sample_paths["rom"],
        definition_path=sample_paths["definition"],
    )

    assert result["status"] == "success"
    assert result["rom_analysis"]["tables_parsed"] > 0
    assert result["datalog_analysis"]["summary"]["total_rows"] > 0
