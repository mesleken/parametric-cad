"""PyTest fixtures and test isolation configuration."""

import os
import pytest
from pathlib import Path

@pytest.fixture(autouse=True)
def isolate_pcad_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolates PCAD data and log directories to a temporary path for every test.
    
    Guarantees tests never read or write to user directories (B11, B23, D11).
    """
    data_dir = tmp_path / "pcad_data"
    log_dir = tmp_path / "pcad_log"
    data_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    monkeypatch.setenv("PCAD_DATA_DIR", str(data_dir))
    monkeypatch.setenv("PCAD_LOG_DIR", str(log_dir))
