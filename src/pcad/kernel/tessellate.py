"""Tessellation of CAD solids into mesh arrays for UI viewport."""

from pathlib import Path
from typing import Tuple
import numpy as np
from build123d import Solid

def tessellate_solid(
    solid: Solid,
    tolerance: float = 0.1,
    angular_tolerance: float = 0.2
) -> Tuple[np.ndarray, np.ndarray]:
    """Tessellates solid into vertex and face triangle index arrays."""
    verts_raw, triangles = solid.tessellate(tolerance=tolerance, angular_tolerance=angular_tolerance)
    # verts can be build123d.Vector objects or tuples
    coords = [(float(v.X), float(v.Y), float(v.Z)) if hasattr(v, "X") else (float(v[0]), float(v[1]), float(v[2])) for v in verts_raw]
    v_arr = np.array(coords, dtype=np.float32)
    # PyVista expects faces formatted as [3, i0, i1, i2, 3, j0, j1, j2, ...]
    n_tri = len(triangles)
    faces_arr = np.empty((n_tri, 4), dtype=np.int32)
    faces_arr[:, 0] = 3
    faces_arr[:, 1:] = triangles
    f_flat = faces_arr.ravel()
    return v_arr, f_flat

def save_mesh_npz(verts: np.ndarray, faces: np.ndarray, path: Path) -> Path:
    """Saves mesh arrays to a compact .npz file for IPC transfer to UI."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(str(path), verts=verts, faces=faces)
    return path
