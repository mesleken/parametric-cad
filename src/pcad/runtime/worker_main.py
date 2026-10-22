"""Worker process entry point. Runs in a separate process for fault isolation."""

import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from build123d import Solid
from pcad.domain.hashing import compute_model_hash
from pcad.domain.materials import Material, MaterialDB
from pcad.domain.template import CheckResult, PhysicsResult
from pcad.kernel.physics import compute_physics
from pcad.kernel.step_io import export_step_file
from pcad.kernel.stl_io import export_stl_file
from pcad.kernel.tessellate import save_mesh_npz, tessellate_solid
from pcad.kernel.validate import validate_solid
from pcad.runtime.protocol import (
    BuildRequest, BuildResult, ExportRequest, ExportResult, WorkerError
)
from pcad.templates.registry import TemplateRegistry

# Cache of recently generated solids: model_hash -> (Solid, params, Material, PhysicsResult, List[CheckResult], verts, faces)
_CACHE: Dict[str, Tuple[Solid, Any, Material, PhysicsResult, list, Any, Any]] = {}

def process_build(req: BuildRequest) -> BuildResult:
    t0 = time.perf_counter()
    reg = TemplateRegistry.get_default_registry()
    mat_db = MaterialDB.get_default_db()
    material = mat_db.get(req.material_id)
    
    if req.source == "template":
        if not req.template_id:
            raise ValueError("Template ID must be specified for template build.")
        spec = reg.get(req.template_id)
        param_cls = spec.param_cls
        param_obj = param_cls(**req.params)
        model_hash = compute_model_hash(
            template_id=spec.id,
            template_version=spec.version,
            params=req.params,
            material_id=material.id,
            loads=req.loads
        )
    else:
        # Code mode execution
        if not req.code:
            raise ValueError("Code content must be provided in code mode.")
        spec = None
        param_obj = None
        model_hash = compute_model_hash(
            template_id="custom_code",
            template_version="1.0",
            params={"code_hash": hash(req.code)},
            material_id=material.id
        )
        
    t_parse = (time.perf_counter() - t0) * 1000.0
    
    # Check cache
    if model_hash in _CACHE:
        solid, _, _, physics, checks, verts, faces = _CACHE[model_hash]
    else:
        t_geom_start = time.perf_counter()
        if req.source == "template":
            raw_part = spec.build_func(param_obj)
        else:
            local_scope: Dict[str, Any] = {}
            exec(req.code, {}, local_scope)
            if "result" in local_scope:
                raw_part = local_scope["result"]
            elif "part" in local_scope:
                raw_part = local_scope["part"]
            else:
                raise ValueError("Script must assign output solid to variable 'result' or 'part'.")
                
        solid = validate_solid(raw_part)
        t_geom = (time.perf_counter() - t_geom_start) * 1000.0
        
        # Physics
        physics = compute_physics(solid, material)
        
        # Engineering checks
        checks = []
        if spec and spec.checks_func:
            checks = spec.checks_func(param_obj, material, physics)
            
        # Tessellation
        tol = 0.05 if req.quality == "export" else 0.15
        verts, faces = tessellate_solid(solid, tolerance=tol)
        
        # Keep in cache (limit 8 items)
        if len(_CACHE) >= 8:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[model_hash] = (solid, param_obj, material, physics, checks, verts, faces)
        
    # Save mesh to temp .npz
    temp_dir = Path(tempfile.gettempdir()) / "pcad_ipc"
    temp_dir.mkdir(parents=True, exist_ok=True)
    mesh_path = temp_dir / f"mesh_{model_hash[:16]}.npz"
    save_mesh_npz(verts, faces, mesh_path)
    
    t_total = (time.perf_counter() - t0) * 1000.0
    
    return BuildResult(
        req_id=req.req_id,
        model_hash=model_hash,
        mesh_path=str(mesh_path),
        physics=physics,
        checks=checks,
        timings_ms={"total": round(t_total, 1), "parse": round(t_parse, 1)}
    )

def process_export(req: ExportRequest) -> ExportResult:
    if req.model_hash not in _CACHE:
        raise ValueError(f"Model hash {req.model_hash} not found in worker cache. Re-generation required.")
    
    solid, param_obj, material, physics, checks, verts, faces = _CACHE[req.model_hash]
    out_path = Path(req.output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    fmt = req.export_format.lower()
    if fmt == "step":
        export_step_file(solid, out_path)
    elif fmt == "stl":
        export_stl_file(
            solid, out_path,
            tolerance=req.linear_deflection,
            angular_tolerance=req.angular_deflection
        )
    elif fmt == "png":
        from pcad.kernel.render_png import render_mesh_to_png
        render_mesh_to_png(verts, faces, out_path)
    elif fmt == "pdf":
        from pcad.kernel.render_png import render_mesh_to_png
        from pcad.report.datasheet import generate_datasheet_pdf
        # First generate a temp PNG for the datasheet image
        temp_png = out_path.with_suffix(".temp_preview.png")
        render_mesh_to_png(verts, faces, temp_png, image_size=(800, 600))
        params_dict = param_obj.model_dump() if hasattr(param_obj, "model_dump") else {}
        generate_datasheet_pdf(
            output_pdf_path=out_path,
            template_name="PCAD Model",
            template_version="1.0.0",
            params=params_dict,
            material=material,
            physics=physics,
            checks=checks,
            model_hash=req.model_hash,
            preview_png_path=temp_png
        )
        if temp_png.exists():
            temp_png.unlink(missing_ok=True)
    else:
        raise ValueError(f"Unsupported export format: {fmt}")
        
    return ExportResult(req_id=req.req_id, output_path=str(out_path), success=True)

def main():
    """Worker main loop reading JSON lines from sys.stdin."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            req_type = data.get("type", "build")
            
            if req_type == "build":
                req = BuildRequest(**data.get("payload", data))
                result = process_build(req)
                resp = {"status": "ok", "type": "build", "payload": result.model_dump()}
            elif req_type == "export":
                req = ExportRequest(**data.get("payload", data))
                result = process_export(req)
                resp = {"status": "ok", "type": "export", "payload": result.model_dump()}
            else:
                resp = {"status": "error", "error": f"Unknown request type '{req_type}'"}
                
        except Exception as e:
            trace = traceback.format_exc()
            err_kind = "geometry_invalid" if "GeometryError" in type(e).__name__ else "param_invalid"
            payload_dict = data.get("payload", data)
            req_id_val = payload_dict.get("req_id", "unknown") if isinstance(payload_dict, dict) else "unknown"
            err = WorkerError(
                req_id=req_id_val,
                kind=err_kind,
                message_key=str(e),
                detail=trace
            )
            resp = {"status": "error", "error": err.model_dump()}
            
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
