"""Physical properties calculator (Volume, mass, CoG, bounding box, inertia)."""

from typing import Tuple
from build123d import Solid
from pcad.domain.materials import Material
from pcad.domain.template import PhysicsResult

def compute_physics(solid: Solid, material: Material) -> PhysicsResult:
    """Computes exact volume, mass, center of gravity, bbox, and moments of inertia."""
    vol_mm3 = float(solid.volume)
    area_mm2 = float(solid.area)
    
    # Mass in grams: density (g/cm3) * volume (mm3) / 1000.0
    mass_g = material.density_g_cm3 * (vol_mm3 / 1000.0)
    
    # Center of gravity in mm
    center = solid.center()
    cog_mm = (float(center.X), float(center.Y), float(center.Z))
    
    # Bounding Box (xmin, ymin, zmin, xmax, ymax, zmax)
    bbox = solid.bounding_box()
    bbox_mm = (
        float(bbox.min.X), float(bbox.min.Y), float(bbox.min.Z),
        float(bbox.max.X), float(bbox.max.Y), float(bbox.max.Z)
    )
    
    # Moment of inertia (matrix diagonal Ixx, Iyy, Izz) in g * mm2
    # In build123d, solid.moment_of_inertia gives volumetric inertia in mm^5.
    # Scaled by density to get physical inertia:
    try:
        raw_inertia = solid.moment_of_inertia
        density_g_mm3 = material.density_g_cm3 / 1000.0
        # Inertia tensor diagonal elements
        ixx = float(raw_inertia[0][0]) * density_g_mm3 if hasattr(raw_inertia, "__getitem__") else 0.0
        iyy = float(raw_inertia[1][1]) * density_g_mm3 if hasattr(raw_inertia, "__getitem__") else 0.0
        izz = float(raw_inertia[2][2]) * density_g_mm3 if hasattr(raw_inertia, "__getitem__") else 0.0
        inertia_tuple = (ixx, iyy, izz)
    except Exception:
        inertia_tuple = (0.0, 0.0, 0.0)
        
    return PhysicsResult(
        volume_mm3=round(vol_mm3, 2),
        mass_g=round(mass_g, 2),
        surface_area_mm2=round(area_mm2, 2),
        cog_mm=(round(cog_mm[0], 2), round(cog_mm[1], 2), round(cog_mm[2], 2)),
        bbox_mm=(round(b, 2) for b in bbox_mm),
        inertia_g_mm2=(round(inertia_tuple[0], 1), round(inertia_tuple[1], 1), round(inertia_tuple[2], 1))
    )
