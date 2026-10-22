"""STL export and mesh quality validation for 3D printing."""

from pathlib import Path
from build123d import Solid, export_stl

def export_stl_file(
    solid: Solid,
    path: Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1
) -> Path:
    """Exports solid to binary STL with specified surface deflection tolerances."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    export_stl(
        solid,
        str(path),
        tolerance=tolerance,
        angular_tolerance=angular_tolerance
    )
    
    # Check that file was created and is non-empty
    if not path.exists() or path.stat().st_size < 84: # Minimal binary STL header size
        raise ValueError(f"Failed to generate valid STL file at {path}")
        
    return path
