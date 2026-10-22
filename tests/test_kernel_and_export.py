"""Unit tests for CAD kernel, STEP normalization, STL, and PDF generation."""

from pathlib import Path
import build123d as bd
import pytest

from pcad.domain.materials import MaterialDB
from pcad.kernel.physics import compute_physics
from pcad.kernel.step_io import export_step_file, verify_step_volume
from pcad.kernel.stl_io import export_stl_file
from pcad.kernel.tessellate import tessellate_solid
from pcad.kernel.validate import validate_solid
from pcad.report.datasheet import generate_datasheet_pdf

def test_solid_validation_and_physics():
    with bd.BuildPart() as p:
        bd.Box(10.0, 20.0, 30.0)
    
    solid = validate_solid(p.part)
    assert solid.is_valid
    assert pytest.approx(solid.volume, 0.01) == 6000.0
    
    mat = MaterialDB.get_default_db().get("Al7075-T6")
    phys = compute_physics(solid, mat)
    # Mass = 2.81 g/cm3 * 6.0 cm3 = 16.86 g
    assert pytest.approx(phys.mass_g, 0.05) == 16.86

def test_step_export_determinism_and_reread(tmp_path: Path):
    with bd.BuildPart() as p:
        bd.Cylinder(radius=10.0, height=25.0)
    solid = validate_solid(p.part)
    
    step_file1 = tmp_path / "model1.step"
    step_file2 = tmp_path / "model2.step"
    
    export_step_file(solid, step_file1, normalize_header=True)
    export_step_file(solid, step_file2, normalize_header=True)
    
    # Check byte-for-byte identity
    with open(step_file1, "rb") as f1, open(step_file2, "rb") as f2:
        assert f1.read() == f2.read()
        
    # Re-read volume
    re_vol = verify_step_volume(step_file1)
    assert pytest.approx(re_vol, 0.01) == solid.volume

def test_stl_and_pdf_generation(tmp_path: Path):
    with bd.BuildPart() as p:
        bd.Box(15.0, 15.0, 15.0)
    solid = validate_solid(p.part)
    
    # STL
    stl_path = tmp_path / "box.stl"
    export_stl_file(solid, stl_path)
    assert stl_path.exists()
    assert stl_path.stat().st_size > 100
    
    # PDF
    pdf_path = tmp_path / "box_sheet.pdf"
    mat = MaterialDB.get_default_db().get("Al7075-T6")
    phys = compute_physics(solid, mat)
    generate_datasheet_pdf(
        output_pdf_path=pdf_path,
        template_name="Test Box",
        template_version="1.0.0",
        params={"size": 15.0},
        material=mat,
        physics=phys,
        checks=[],
        model_hash="box123"
    )
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000
