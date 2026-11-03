"""Tests for Splice Plate template and architectural resilience."""

import pytest
from pydantic import ValidationError

from pcad.domain.materials import MaterialDB
from pcad.domain.template import MarginStatus
from pcad.kernel.physics import compute_physics
from pcad.kernel.validate import validate_solid
from pcad.templates.builtin.aero.splice_plate import SplicePlateParams, build, checks

def test_splice_plate_validation():
    # Valid params
    p = SplicePlateParams(
        plate_length=180.0,
        plate_width=70.0,
        plate_thickness=6.0,
        bolt_dia=10.0,
        rows=2,
        cols_per_side=2,
        pitch_x=35.0,
        gauge_y=35.0,
        edge_x=25.0
    )
    assert p.plate_length == 180.0
    
    # Invalid: bolt pattern exceeds width
    with pytest.raises(ValidationError):
        SplicePlateParams(plate_width=30.0, bolt_dia=10.0, rows=3, gauge_y=20.0)

def test_splice_plate_geometry_and_checks():
    p = SplicePlateParams()
    raw_part = build(p)
    solid = validate_solid(raw_part)
    assert solid.is_valid
    assert solid.volume > 1000.0
    
    mat = MaterialDB.get_default_db().get("Al7075-T6")
    phys = compute_physics(solid, mat)
    assert phys.mass_g > 0.0
    
    res = checks(p, mat, phys)
    assert len(res) == 5
    
    net_chk = next(c for c in res if c.name == "Net-Section Tension")
    assert net_chk.status == MarginStatus.POSITIVE
    assert net_chk.applied > 0.0
    
    shear_chk = next(c for c in res if "Fastener Shear Stress" in c.name)
    assert shear_chk.status == MarginStatus.POSITIVE
    assert shear_chk.applied > 0.0
    
    ed_chk = next(c for c in res if "Edge Distance" in c.name)
    assert ed_chk.applied == 2.5 # 20 / 8 = 2.5 >= 2.0
    assert ed_chk.status == MarginStatus.POSITIVE

def test_layer_boundary_isolation():
    """Verifies that importing domain models does not pull in heavy Qt/GUI frameworks."""
    import sys
    # Verify that pcad.domain.template does not depend on PySide6
    from pcad.domain.template import TemplateSpec, PhysicsResult, CheckResult
    assert "PySide6.QtWidgets" not in sys.modules
