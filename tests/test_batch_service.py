"""Tests for the Batch CSV parametric generation service."""

import csv
import pytest
from pathlib import Path
from pcad.services.batch_service import BatchService

def test_batch_service_sample_csv(tmp_path):
    service = BatchService()
    sample_csv = tmp_path / "sample_shaft.csv"
    service.generate_sample_csv("mech.stepped_shaft", sample_csv)
    
    assert sample_csv.exists()
    with open(sample_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) >= 2
        assert "d1" in reader[0]
        assert "d2" in reader[0]
        assert "torque_nm" in reader[0]

def test_batch_service_execution(tmp_path):
    service = BatchService()
    csv_file = tmp_path / "flange_batch.csv"
    
    # Write 3 rows: 2 valid, 1 invalid (OD < ID)
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["outer_dia", "inner_dia", "flange_thickness", "neck_height", "neck_outer_dia", "pcd", "num_bolts", "bolt_hole_dia", "fillet_radius"])
        # Row 1: Valid standard
        writer.writerow([120, 40, 16, 30, 60, 90, 4, 12, 4])
        # Row 2: Valid large
        writer.writerow([160, 50, 20, 35, 75, 120, 6, 14, 5])
        # Row 3: Invalid (PCD exceeds outer_dia)
        writer.writerow([100, 30, 14, 25, 50, 110, 4, 10, 3])

    out_dir = tmp_path / "batch_out"
    summary = service.run_batch(
        template_id="demo.flange",
        csv_path=csv_file,
        output_dir=out_dir,
        material_id="AISI4140",
        export_step=True,
        export_stl=False
    )

    assert summary.total_rows == 3
    assert summary.successful_count == 2
    assert summary.failed_count == 1
    assert (out_dir / "batch_report.csv").exists()
    assert (out_dir / "batch_report.json").exists()
    
    # Verify STEP file was created for row 1
    assert summary.results[0].status == "success"
    assert summary.results[0].step_path is not None
    assert Path(summary.results[0].step_path).exists()
    
    # Verify Row 3 failed with validation error
    assert summary.results[2].status == "validation_failed"
    assert "Bolt circle holes exceed outer flange boundary" in summary.results[2].error_message
