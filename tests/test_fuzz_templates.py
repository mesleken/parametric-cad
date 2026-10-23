"""Fuzz and parameter variance testing across all built-in templates."""

import random
import pytest
from pydantic.fields import FieldInfo
from pcad.domain.materials import MaterialDB
from pcad.kernel.physics import compute_physics
from pcad.kernel.validate import validate_solid
from pcad.templates.registry import TemplateRegistry

def test_all_builtin_templates_default_generation():
    """Verify that every single registered template builds a valid 3D solid with its defaults."""
    reg = TemplateRegistry.get_default_registry()
    templates = reg.list_templates()
    assert len(templates) >= 8, f"Expected at least 8 built-in templates, found {len(templates)}"
    
    mat_db = MaterialDB.get_default_db()
    
    for tpl in templates:
        param_cls = tpl.param_cls
        default_params = param_cls()
        part = tpl.build_func(default_params)
        solid = validate_solid(part)
        
        # Valid non-zero volume
        assert solid.volume > 10.0, f"Template {tpl.id} produced negligible volume: {solid.volume}"
        
        # Physics calculation
        mat = mat_db.get(tpl.default_material)
        physics = compute_physics(solid, mat)
        assert physics.mass_g > 0.0
        
        # Engineering checks (if defined)
        if tpl.checks_func:
            checks = tpl.checks_func(default_params, mat, physics)
            assert len(checks) > 0, f"Checks function defined but empty for {tpl.id}"
            for c in checks:
                assert c.status in ("POSITIVE", "LOW", "NEGATIVE")

def test_fuzz_flange_variations():
    """Fuzz weld-neck flange with multiple randomized dimension variations."""
    reg = TemplateRegistry.get_default_registry()
    tpl = reg.get("demo.flange")
    
    # 5 safe parameter variations
    variations = [
        {"outer_dia": 100.0, "inner_dia": 30.0, "flange_thickness": 12.0, "neck_height": 20.0, "neck_outer_dia": 50.0, "pcd": 75.0, "num_bolts": 4, "bolt_hole_dia": 10.0, "fillet_radius": 2.0},
        {"outer_dia": 160.0, "inner_dia": 60.0, "flange_thickness": 20.0, "neck_height": 40.0, "neck_outer_dia": 80.0, "pcd": 120.0, "num_bolts": 8, "bolt_hole_dia": 14.0, "fillet_radius": 4.0},
        {"outer_dia": 220.0, "inner_dia": 80.0, "flange_thickness": 25.0, "neck_height": 50.0, "neck_outer_dia": 110.0, "pcd": 165.0, "num_bolts": 12, "bolt_hole_dia": 16.0, "fillet_radius": 5.0},
    ]
    
    for var in variations:
        params = tpl.param_cls(**var)
        part = tpl.build_func(params)
        solid = validate_solid(part)
        assert solid.volume > 1000.0

def test_fuzz_spur_gear_variations():
    """Fuzz true involute spur gear with different tooth counts and face widths."""
    reg = TemplateRegistry.get_default_registry()
    tpl = reg.get("mech.spur_gear")
    
    variations = [
        {"module": 1.5, "num_teeth": 18, "face_width": 15.0, "bore_dia": 10.0, "hub_dia": 20.0, "hub_length": 8.0, "torque_nm": 10.0},
        {"module": 3.0, "num_teeth": 30, "face_width": 25.0, "bore_dia": 20.0, "hub_dia": 40.0, "hub_length": 15.0, "torque_nm": 40.0},
        {"module": 2.0, "num_teeth": 36, "face_width": 20.0, "bore_dia": 15.0, "hub_dia": 35.0, "hub_length": 10.0, "torque_nm": 20.0},
    ]
    
    for var in variations:
        params = tpl.param_cls(**var)
        part = tpl.build_func(params)
        solid = validate_solid(part)
        assert solid.volume > 500.0

def test_default_margins_are_non_negative():
    """Verify that default parameter configurations on load do not present negative margins."""
    reg = TemplateRegistry.get_default_registry()
    mat_db = MaterialDB.get_default_db()
    
    for tpl in reg.list_templates():
        if tpl.checks_func:
            params = tpl.param_cls()
            mat = mat_db.get(tpl.default_material)
            solid = validate_solid(tpl.build_func(params))
            physics = compute_physics(solid, mat)
            checks = tpl.checks_func(params, mat, physics)
            for c in checks:
                assert c.status != "NEGATIVE", f"Default check {c.name} for {tpl.id} is NEGATIVE (margin={c.margin_of_safety})"
