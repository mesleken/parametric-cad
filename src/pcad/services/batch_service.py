"""Batch CSV processing service for multi-variant parametric CAD generation."""

import csv
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel

from pcad.domain.hashing import compute_model_hash
from pcad.domain.materials import MaterialDB
from pcad.kernel.step_io import export_step_file
from pcad.kernel.stl_io import export_stl_file
from pcad.services.model_service import ModelRequest, ModelService
from pcad.templates.registry import TemplateRegistry

class BatchRowResult(BaseModel):
    row_index: int
    params: Dict[str, Any]
    status: str # "success", "validation_failed", "geometry_failed"
    model_hash: Optional[str] = None
    step_path: Optional[str] = None
    stl_path: Optional[str] = None
    mass_g: Optional[float] = None
    volume_mm3: Optional[float] = None
    duration_ms: float = 0.0
    error_message: Optional[str] = None

class BatchSummary(BaseModel):
    template_id: str
    total_rows: int
    successful_count: int
    failed_count: int
    total_duration_sec: float
    output_directory: str
    results: List[BatchRowResult]

class BatchService:
    def __init__(self, registry: Optional[TemplateRegistry] = None, mat_db: Optional[MaterialDB] = None):
        self.registry = registry or TemplateRegistry.get_default_registry()
        self.mat_db = mat_db or MaterialDB.get_default_db()
        self.model_service = ModelService(self.registry, self.mat_db)

    def generate_sample_csv(self, template_id: str, out_path: Path) -> Path:
        """Generates a sample CSV template for the given CAD template with default values."""
        spec = self.registry.get(template_id)
        param_cls = spec.param_cls
        default_obj = param_cls()
        fields = list(param_cls.model_fields.keys())
        
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            # Row 1: defaults
            writer.writerow(default_obj.model_dump())
            # Row 2: slight variation (+10% on first numeric field if exists)
            row2 = default_obj.model_dump()
            for k, v in row2.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    row2[k] = round(v * 1.1, 2)
                    break
            writer.writerow(row2)
        return out_path

    def run_batch(
        self,
        template_id: str,
        csv_path: Path,
        output_dir: Path,
        material_id: str = "Al7075-T6",
        export_step: bool = True,
        export_stl: bool = True,
        progress_callback: Optional[Callable[[int, int, BatchRowResult], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> BatchSummary:
        """Executes batch production for each row in the CSV file."""
        spec = self.registry.get(template_id)
        param_cls = spec.param_cls
        material = self.mat_db.get(material_id)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read CSV rows
        rows: List[Dict[str, Any]] = []
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Clean up whitespace
                clean_row = {k.strip(): v.strip() for k, v in r.items() if k is not None}
                rows.append(clean_row)

        total_rows = len(rows)
        results: List[BatchRowResult] = []
        t0_total = time.perf_counter()

        for idx, raw_row in enumerate(rows, 1):
            if cancel_check and cancel_check():
                break

            t0_row = time.perf_counter()
            row_params: Dict[str, Any] = {}
            row_res: BatchRowResult

            # 1. Parse and cast types according to Pydantic field annotations
            try:
                for field_name, field_info in param_cls.model_fields.items():
                    if field_name not in raw_row or raw_row[field_name] == "":
                        # Use default if available
                        if field_info.default is not None:
                            row_params[field_name] = field_info.default
                        continue
                        
                    val_str = raw_row[field_name]
                    target_type = field_info.annotation
                    
                    if target_type is int or target_type == int:
                        row_params[field_name] = int(float(val_str))
                    elif target_type is float or target_type == float:
                        row_params[field_name] = float(val_str)
                    elif target_type is bool or target_type == bool:
                        row_params[field_name] = val_str.lower() in ("true", "1", "yes", "t")
                    else:
                        row_params[field_name] = val_str
                        
                # 2. Validate row with Pydantic
                param_obj = param_cls(**row_params)
                
            except Exception as e:
                dur = (time.perf_counter() - t0_row) * 1000.0
                row_res = BatchRowResult(
                    row_index=idx,
                    params=row_params or raw_row,
                    status="validation_failed",
                    duration_ms=round(dur, 1),
                    error_message=f"Parameter Validation Error: {e}"
                )
                results.append(row_res)
                if progress_callback:
                    progress_callback(idx, total_rows, row_res)
                continue

            # 3. Build geometry and compute physics via unified ModelService (D5, D7)
            try:
                resp = self.model_service.generate(ModelRequest(
                    source="template",
                    template_id=spec.id,
                    params=param_obj.model_dump(),
                    material_id=material.id
                ))
                solid = resp.solid
                phys = resp.physics
                model_hash = resp.model_hash
                
                step_file = None
                stl_file = None
                file_prefix = f"part_{idx:03d}_{model_hash[:8]}"
                
                if export_step:
                    step_file = output_dir / f"{file_prefix}.step"
                    export_step_file(solid, step_file)
                    
                if export_stl:
                    stl_file = output_dir / f"{file_prefix}.stl"
                    export_stl_file(solid, stl_file)
                    
                dur = (time.perf_counter() - t0_row) * 1000.0
                row_res = BatchRowResult(
                    row_index=idx,
                    params=param_obj.model_dump(),
                    status="success",
                    model_hash=model_hash,
                    step_path=str(step_file) if step_file else None,
                    stl_path=str(stl_file) if stl_file else None,
                    mass_g=round(phys.mass_g, 2),
                    volume_mm3=round(phys.volume_mm3, 1),
                    duration_ms=round(dur, 1)
                )
                
            except Exception as e:
                dur = (time.perf_counter() - t0_row) * 1000.0
                row_res = BatchRowResult(
                    row_index=idx,
                    params=param_obj.model_dump(),
                    status="geometry_failed",
                    duration_ms=round(dur, 1),
                    error_message=f"CAD Kernel Error: {e}"
                )

            results.append(row_res)
            if progress_callback:
                progress_callback(idx, total_rows, row_res)

        total_dur = time.perf_counter() - t0_total
        success_count = sum(1 for r in results if r.status == "success")
        fail_count = len(results) - success_count

        summary = BatchSummary(
            template_id=template_id,
            total_rows=len(results),
            successful_count=success_count,
            failed_count=fail_count,
            total_duration_sec=round(total_dur, 2),
            output_directory=str(output_dir),
            results=results
        )

        # Write summary files
        self._write_reports(summary, output_dir)
        return summary

    def _write_reports(self, summary: BatchSummary, output_dir: Path):
        """Writes summary report in both CSV and JSON formats."""
        # 1. JSON Report
        json_path = output_dir / "batch_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(summary.model_dump_json(indent=2))

        # 2. CSV Summary
        csv_path = output_dir / "batch_report.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            fields = ["Row", "Status", "Mass_g", "Volume_mm3", "Duration_ms", "STEP_File", "STL_File", "Error_Message"]
            writer = csv.writer(f)
            writer.writerow(fields)
            for r in summary.results:
                writer.writerow([
                    r.row_index,
                    r.status,
                    r.mass_g if r.mass_g is not None else "",
                    r.volume_mm3 if r.volume_mm3 is not None else "",
                    r.duration_ms,
                    Path(r.step_path).name if r.step_path else "",
                    Path(r.stl_path).name if r.stl_path else "",
                    r.error_message or ""
                ])
