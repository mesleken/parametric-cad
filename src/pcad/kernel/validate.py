"""Geometry validation for manifold solids."""

from typing import Optional, Union
from build123d import Compound, Part, Shape, Solid
from pcad.domain.errors import GeometryError

def validate_solid(shape_or_part, allow_multiple: bool = False) -> Union[Solid, Compound]:
    """Validates that the generated object is a non-empty, valid manifold solid.
    
    By default (allow_multiple=False), enforces a single unified solid body.
    Multiple disconnected solids will raise GeometryError unless allow_multiple=True.
    """
    if hasattr(shape_or_part, "solids") and shape_or_part.solids():
        solids = shape_or_part.solids()
        if len(solids) > 1 and not allow_multiple:
            raise GeometryError(
                "err.multiple_solids",
                f"Model separated into {len(solids)} disconnected solid bodies; expected a single unified solid."
            )
        solid = solids[0] if len(solids) == 1 else Compound(solids)
    elif isinstance(shape_or_part, (Solid, Part, Shape, Compound)):
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
