"""Unified path resolution for PCAD.

Supports environment variables:
- PCAD_DATA_DIR: overrides user data directory
- PCAD_LOG_DIR: overrides user log directory
"""

import os
from pathlib import Path
import platformdirs

def get_user_data_dir() -> Path:
    """Returns the PCAD user data directory (creates if missing)."""
    env_dir = os.environ.get("PCAD_DATA_DIR")
    if env_dir:
        p = Path(env_dir)
    else:
        p = Path(platformdirs.user_data_dir("pcad", "pcad"))
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_user_templates_dir() -> Path:
    """Returns the user custom templates directory."""
    tpl_dir = get_user_data_dir() / "templates"
    tpl_dir.mkdir(parents=True, exist_ok=True)
    return tpl_dir

def get_user_log_dir() -> Path:
    """Returns the PCAD log directory."""
    env_dir = os.environ.get("PCAD_LOG_DIR")
    if env_dir:
        p = Path(env_dir)
    else:
        p = Path(platformdirs.user_log_dir("pcad", "pcad"))
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_package_data_dir() -> Path:
    """Returns the built-in package data directory."""
    return Path(__file__).resolve().parent.parent / "domain" / "data"
