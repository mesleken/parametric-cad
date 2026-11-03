"""Golden Reference and Analytical Physics Tests (F1, F4).

Compares physics, inertia, and engineering calculations against exact analytical formulas:
1. Analytical inertia moments of canonical rectangular prism.
2. Flange analytical volume accounting for through bore cylinder without top plug (B7).
3. Lug tip distance matching edge distance parameter e (B6).
4. Shaft minimum diameter stress evaluation (B4).
5. Strict MaterialDB error handling without fallback (B3).
"""

import math
import pytest
from build123d import Box, Solid
from pcad.domain.materials import Material, MaterialDB
from pcad.engineering.shaft_checks import check_stepped_shaft
from pcad.kernel.physics import compute_physics
from pcad.kernel.validate import validate_solid
from pcad.templates.registry import TemplateRegistry

def test_analytical_inertia_tensor():
    """Verify compute_physics inertia matches exact analytical formula I = (1/12)*m*(a^2+b^2)."""
    # Box: X=10, Y=20, Z=30 mm
    box = Solid.make_box(10.0, 20.0, 30.0)
    # Center box at origin so central principal moments match axis
    box = box.translate((-5.0, -10.0, -15.0))
    
    mat = Material(
        id="TestMat",
        name="Test",
        density_g_cm3=2.81,
        yield_strength_mpa=500.0,
        ultimate_strength_mpa=550.0,
        shear_strength_mpa=300.0
    )
    
    phys = compute_physics(box, mat)
    # Mass = 10 * 20 * 30 * 0.00281 = 16.86 g
    assert abs(phys.mass_g - 16.86) < 1e-2
    
    # Analytical moments:
    # Ixx = (1/12) * 16.86 * (20^2 + 30^2) = 1826.5 g*mm^2
    # Iyy = (1/12) * 16.86 * (10^2 + 30^2) = 1405.0 g*mm^2
    # Izz = (1/12) * 16.86 * (10^2 + 20^2) = 702.5 g*mm^2
    ixx, iyy, izz = phys.inertia_g_mm2
    assert abs(ixx - 1826.5) < 1.0, f"Ixx {ixx} does not match analytical 1826.5"
    assert abs(iyy - 1405.0) < 1.0, f"Iyy {iyy} does not match analytical 1405.0"
    assert abs(izz - 702.5) < 1.0, f"Izz {izz} does not match analytical 702.5"


def test_flange_analytical_volume():
    """Verify demo.flange volume matches analytical calculation within 0.1% (B7)."""
    reg = TemplateRegistry.get_default_registry()
    spec = reg.get("demo.flange")
    p = spec.param_cls()
    solid = validate_solid(spec.build_func(p))
    
    # Analytical volume:
    v_base = math.pi * ((p.outer_dia / 2.0) ** 2) * p.flange_thickness
    v_neck = math.pi * ((p.neck_outer_dia / 2.0) ** 2) * p.neck_height
    v_bore = math.pi * ((p.inner_dia / 2.0) ** 2) * (p.flange_thickness + p.neck_height)
    v_bolts = p.num_bolts * math.pi * ((p.bolt_hole_dia / 2.0) ** 2) * p.flange_thickness
    analytical = v_base + v_neck - v_bore - v_bolts
    rel_diff = abs(solid.volume - analytical) / analytical
    assert rel_diff < 0.001, f"Volume {solid.volume} deviates from analytical {analytical} by {rel_diff*100:.3f}%"


def test_lug_edge_distance_consistency():
    """Verify aero.lug tip distance from hole center equals edge distance e (B6)."""
    reg = TemplateRegistry.get_default_registry()
    spec = reg.get("aero.lug")
    p = spec.param_cls(W=40.0, D=12.0, e=24.0, stem_height=30.0, base_thickness=10.0)
    solid = validate_solid(spec.build_func(p))
    
    bbox = solid.bounding_box()
    # Hole center is at Z = base_thickness + stem_height = 10 + 30 = 40.0
    hole_z = 10.0 + 30.0
    tip_z = bbox.max.Z
    actual_e = tip_z - hole_z
    assert abs(actual_e - p.e) < 1e-2, f"Actual edge distance {actual_e} does not match p.e {p.e}"


def test_stepped_shaft_minimum_diameter_stress():
    """Verify check_stepped_shaft evaluates shear on min(d1, d3) (B4)."""
    reg = TemplateRegistry.get_default_registry()
    spec = reg.get("mech.stepped_shaft")
    mat = Material(
        id="Steel",
        name="Steel",
        density_g_cm3=7.85,
        yield_strength_mpa=600.0,
        ultimate_strength_mpa=800.0,
        shear_strength_mpa=350.0
    )
    # d1 = 30.0, d2 = 40.0, d3 = 20.0 -> minimum is d3 = 20.0
    p = spec.param_cls(d1=30.0, d2=40.0, d3=20.0, torque_nm=100.0, fos=1.5)
    solid = validate_solid(spec.build_func(p))
    phys = compute_physics(solid, mat)
    checks = check_stepped_shaft(p, mat, phys)
    
    torsion_check = next(c for c in checks if "Torsional Shear Stress" in c.name)
    # Tau = (16 * T) / (pi * d_min^3)
    # d_min = 20.0 mm -> W_p = (pi * 20^3) / 16 = 1570.8 mm^3
    # Tau = (100 * 1000) / 1570.8 = 63.66 MPa
    expected_tau = (16.0 * 100.0 * 1000.0) / (math.pi * (20.0 ** 3))
    assert abs(torsion_check.applied - expected_tau) < 0.1, f"Expected {expected_tau:.2f}, got {torsion_check.applied:.2f}"


def test_material_db_strict_lookup():
    """Verify MaterialDB raises KeyError on unknown material (B3)."""
    db = MaterialDB.get_default_db()
    with pytest.raises(KeyError):
        db.get("NonExistentMaterial_XYZ_123")
