"""Geometry validation for manifold solids."""

from typing import Tuple
from build123d import Part, Shape, Solid
from pcad.domain.errors import GeometryError

def validate_solid(shape_or_part):
    """Validates that the generated object is a non-empty, valid manifold solid."""
    if hasattr(shape_or_part, "solids") and shape_or_part.solids():
        solid = shape_or_part.solids()[0]
    elif isinstance(shape_or_part, (Solid, Part, Shape)):
        solid = shape_or_part
    else:
        raise GeometryError("err.invalid_geometry", "Output object does not contain a valid 3D solid.")

    valid_status = solid.is_valid() if callable(getattr(solid, "is_valid", None)) else getattr(solid, "is_valid", True)
    if not valid_status:
        raise GeometryError("err.invalid_geometry", "Solid topology is invalid according to OpenCascade B-Rep.")

    vol = solid.volume
    if vol <= 1e-4:
        raise GeometryError("err.invalid_geometry", f"Solid has zero or negative volume ({vol:.4f} mm3).")

    return solid
