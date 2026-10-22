"""Unit tests for domain models, hashing, and project persistence."""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from pcad.domain.hashing import compute_model_hash
from pcad.domain.materials import MaterialDB
from pcad.domain.project import ProjectData, load_project, save_project
from pcad.templates.builtin.demo.flange import FlangeParams
from pcad.templates.builtin.aero.lug import LugParams

def test_flange_params_validation():
    # Valid params
    p = FlangeParams(outer_dia=150.0, inner_dia=50.0, neck_outer_dia=70.0, pcd=110.0, bolt_hole_dia=12.0)
    assert p.outer_dia == 150.0
    
    # Invalid: ID >= neck_outer_dia
    with pytest.raises(ValidationError):
        FlangeParams(outer_dia=150.0, inner_dia=80.0, neck_outer_dia=70.0)

def test_lug_params_validation():
    # Valid params
    p = LugParams(W=50.0, D=15.0, e=30.0, t=10.0)
    assert p.W == 50.0
    
    # Invalid: D >= W
    with pytest.raises(ValidationError):
        LugParams(W=20.0, D=25.0, e=20.0, t=5.0)
        
    # Invalid: e <= D/2
    with pytest.raises(ValidationError):
        LugParams(W=40.0, D=12.0, e=5.0, t=8.0)

def test_material_database():
    db = MaterialDB.get_default_db()
    mats = db.list_materials()
    assert len(mats) >= 5
    
    al7075 = db.get("Al7075-T6")
    assert al7075.density_g_cm3 == 2.81
    assert al7075.ultimate_strength_mpa == 572.0

def test_model_hashing_determinism():
    h1 = compute_model_hash("aero.lug", "1.0", {"W": 40.0, "D": 12.0}, "Al7075-T6")
    # Same params in different key insertion order
    h2 = compute_model_hash("aero.lug", "1.0", {"D": 12.0, "W": 40.0}, "Al7075-T6")
    assert h1 == h2
    assert len(h1) == 64

def test_project_save_and_load(tmp_path: Path):
    proj_file = tmp_path / "test_case.pcad"
    data = ProjectData(
        template_id="aero.lug",
        template_version="1.0.0",
        params={"W": 45.0, "D": 14.0, "e": 28.0, "t": 10.0},
        material_id="Ti6Al4V",
        model_hash="abc12345"
    )
    save_project(data, proj_file)
    assert proj_file.exists()
    
    loaded = load_project(proj_file)
    assert loaded.template_id == "aero.lug"
    assert loaded.params["W"] == 45.0
    assert loaded.material_id == "Ti6Al4V"
