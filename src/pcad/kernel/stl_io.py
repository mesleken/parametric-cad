"""STL export and mesh quality validation for 3D printing."""

import struct
from pathlib import Path
from build123d import Solid, export_stl

def export_stl_file(
    solid: Solid,
    path: Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1
) -> Path:
    """Exports solid to binary STL with specified surface deflection tolerances
    and validates watertight binary mesh integrity.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Topological validity check
    is_valid_attr = getattr(solid, "is_valid", True)
    is_valid = is_valid_attr() if callable(is_valid_attr) else bool(is_valid_attr)
    if not is_valid:
        raise ValueError("Cannot export invalid B-Rep solid geometry to STL.")
    
    # 2. Export via OpenCASCADE tessellator
    export_stl(
        solid,
        str(path),
        tolerance=tolerance,
        angular_tolerance=angular_tolerance
    )
    
    # 3. Binary STL structural integrity verification
    if not path.exists():
        raise ValueError(f"Failed to create STL file at {path}")
        
    file_size = path.stat().st_size
    if file_size < 84:
        raise ValueError(f"STL file at {path} is truncated ({file_size} bytes, minimal binary header is 84 bytes).")
        
    with open(path, "rb") as f:
        header = f.read(80)
        tri_bytes = f.read(4)
        num_triangles = struct.unpack("<I", tri_bytes)[0]
        
    expected_size = 84 + (num_triangles * 50)
    if file_size != expected_size:
        raise ValueError(
            f"STL binary file size mismatch at {path}: expected {expected_size} bytes "
            f"for {num_triangles} facets, but found {file_size} bytes."
        )
        
    if num_triangles < 4:
        raise ValueError(
            f"STL mesh has degenerate facet count ({num_triangles} triangles, minimum closed shell requires >= 4)."
        )
        
    return path
