import pytest
from pathlib import Path
from .rom_integration import ROMIntegrationManager
from .test_real_files import sample_paths


def test_extract_raw_tables(sample_paths):
    manager = ROMIntegrationManager()
    tables = manager.extract_raw_tables(
        tune_path=sample_paths["rom"],
        definition_path=sample_paths["definition"],
    )
    assert isinstance(tables, dict)
    assert len(tables) > 0
