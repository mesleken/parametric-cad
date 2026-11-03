"""Geometric and Engineering Invariants Test Suite (F1, F4, D2).

Verifies fundamental physical and topological invariants across all 8 built-in templates:
1. Exactly one manifold solid body (no disconnected bodies or multi-solids).
2. Strictly positive volume and mass.
3. Center of Gravity lies within the bounding box envelope.
4. Inertia diagonal elements are strictly positive (Ixx, Iyy, Izz > 0).
"""

import pytest
from build123d import Solid
from pcad.domain.materials import MaterialDB
from pcad.kernel.physics import compute_physics
from pcad.kernel.validate import validate_solid
from pcad.templates.registry import TemplateRegistry

@pytest.fixture(scope="module")
def registry():
    return TemplateRegistry.get_default_registry()

@pytest.fixture(scope="module")
def material():
    return MaterialDB.get_default_db().get("Al7075-T6")

ALL_TEMPLATES = [
    "demo.flange",
    "aero.lug",
    "aero.clevis",
    "aero.bracket",
    "aero.splice_plate",
    "mech.stepped_shaft",
    "mech.spur_gear",
    "mech.enclosure"
]

@pytest.mark.parametrize("tpl_id", ALL_TEMPLATES)
def test_template_default_invariants(registry, material, tpl_id):
    spec = registry.get(tpl_id)
    param_obj = spec.param_cls()
    
    # 1. Geometry generation and single solid enforcement
    raw = spec.build_func(param_obj)
    solid = validate_solid(raw, allow_multiple=False)
    assert isinstance(solid, Solid)
    assert solid.is_valid
    assert len(solid.solids()) == 1, f"Template {tpl_id} produced {len(solid.solids())} disconnected solids"

    # 2. Volume and physics sanity
    phys = compute_physics(solid, material)
    assert phys.volume_mm3 > 0.0
    assert phys.mass_g > 0.0

    # 3. Center of Gravity within bounding box
    bbox = solid.bounding_box()
    cog = phys.cog_mm
    tol = 1e-3
    assert bbox.min.X - tol <= cog[0] <= bbox.max.X + tol, f"CoG X {cog[0]} outside [{bbox.min.X}, {bbox.max.X}]"
    assert bbox.min.Y - tol <= cog[1] <= bbox.max.Y + tol, f"CoG Y {cog[1]} outside [{bbox.min.Y}, {bbox.max.Y}]"
    assert bbox.min.Z - tol <= cog[2] <= bbox.max.Z + tol, f"CoG Z {cog[2]} outside [{bbox.min.Z}, {bbox.max.Z}]"

    # 4. Inertia moments strictly positive
    ixx, iyy, izz = phys.inertia_g_mm2
    assert ixx > 0.0, f"Ixx non-positive: {ixx}"
    assert iyy > 0.0, f"Iyy non-positive: {iyy}"
    assert izz > 0.0, f"Izz non-positive: {izz}"

    # 5. Engineering checks evaluate without crashing
    if spec.checks_func:
        checks = spec.checks_func(param_obj, material, phys)
        assert isinstance(checks, list)
        assert len(checks) > 0


def test_clevis_shank_connectivity(registry, material):
    """Specific regression test for B1: clevis slot cut must not slice shank."""
    spec = registry.get("aero.clevis")
    p = spec.param_cls(shank_dia=20.0, shank_length=40.0)
    raw = spec.build_func(p)
    solid = validate_solid(raw, allow_multiple=False)
    assert len(solid.solids()) == 1
    # Check bottom shank is intact at Z = -40
    bbox = solid.bounding_box()
    assert abs(bbox.min.Z - (-40.0)) < 1e-3


def test_gusset_bracket_rib_scaling(registry, material):
    """Specific regression test for B5: volume must strictly scale with gusset count."""
    spec = registry.get("aero.bracket")
    vols = []
    for count in [0, 1, 2, 3]:
        p = spec.param_cls(gusset_count=count)
        solid = validate_solid(spec.build_func(p))
        vols.append(solid.volume)
    
    assert vols[1] > vols[0], "1 gusset must have more volume than 0 gussets"
    assert vols[2] > vols[1], "2 gussets must have more volume than 1 gusset"
    assert vols[3] > vols[2], "3 gussets must have more volume than 2 gussets"


def test_stepped_shaft_keyway_confinement(registry, material):
    """Specific regression test for B8: keyway must be confined to journal 1."""
    spec = registry.get("mech.stepped_shaft")
    p = spec.param_cls(keyway_len=20.0, length_1=40.0)
    solid = validate_solid(spec.build_func(p))
    assert len(solid.solids()) == 1
    assert solid.is_valid
