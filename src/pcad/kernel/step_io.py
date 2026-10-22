"""STEP export and normalization for deterministic CAD exchange."""

import re
from pathlib import Path
from build123d import Solid, export_step, import_step

def export_step_file(solid: Solid, path: Path, normalize_header: bool = True) -> Path:
    """Exports solid to STEP AP214 format with optional deterministic header normalization."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Export standard STEP via build123d
    export_step(solid, str(path))
    
    if normalize_header and path.exists():
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # Replace timestamp and dynamic filename in STEP header for deterministic checksums
        # Example line: FILE_NAME('test.step','2026-10-22T14:50:35',(''),(''),'','','');
        normalized = re.sub(
            r"FILE_NAME\([^;]+;",
            "FILE_NAME('pcad_model.step','1970-01-01T00:00:00',('pcad'),('pcad'),'','pcad','');",
            content
        )
        # Also normalize product name derived from filename
        normalized = re.sub(r"PRODUCT\('[^']+',", "PRODUCT('pcad_model',", normalized)
        # Also normalize OpenCascade in-session occurrence sequence counter
        normalized = re.sub(r"_USAGE_OCCURRENCE\('[0-9]+',", "_USAGE_OCCURRENCE('1',", normalized)
        with open(path, "w", encoding="utf-8") as f:
            f.write(normalized)
            
    return path

def verify_step_volume(path: Path) -> float:
    """Reads back exported STEP file and returns volume for verification."""
    shape = import_step(str(path))
    return float(shape.volume)
