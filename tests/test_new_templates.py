"""Unit tests for the new mechanical templates (Stepped Shaft, Spur Gear, Enclosure)."""

import pytest
from pcad.templates.builtin.mech.stepped_shaft import SteppedShaftParams, build as build_shaft
from pcad.templates.builtin.mech.spur_gear import SpurGearParams, build as build_gear
from pcad.templates.builtin.mech.enclosure import EnclosureParams, build as build_enclosure
from pcad.domain.materials import MaterialDB
from pcad.kernel.validate import validate_solid
from pcad.kernel.physics import compute_physics

def test_stepped_shaft():
    # Valid default params
    p = SteppedShaftParams()
    solid = validate_solid(build_shaft(p))
    assert solid.volume > 50000.0
    
    # Proportion validation: shoulder d2 must be > d1
    with pytest.raises(ValueError, match="Central shoulder diameter"):
        SteppedShaftParams(d1=40.0, d2=30.0)

def test_spur_gear():
    p = SpurGearParams()
    solid = validate_solid(build_gear(p))
    assert solid.volume > 20000.0
    
    # Interference validation: hub_dia interfering with root diameter
    with pytest.raises(ValueError, match="Hub diameter"):
        SpurGearParams(module=1.0, num_teeth=12, hub_dia=50.0)

def test_enclosure():
    p = EnclosureParams()
    solid = validate_solid(build_enclosure(p))
    assert solid.volume > 30000.0
    
    # Boundary validation: wall thickness too large
    with pytest.raises(ValueError, match="Wall thickness is too large"):
        EnclosureParams(width=30.0, length=40.0, wall_thickness=20.0)
