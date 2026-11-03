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
from pcad.domain.errors import GeometryError
from pcad.domain.hashing import compute_model_hash, compute_code_model_hash
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

class CodeExecError(Exception):
    def __init__(self, worker_error: WorkerError):
        super().__init__(worker_error.message_key)
        self.worker_error = worker_error

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
        # Code mode execution (B10: canonical SHA-256 code hash)
        if not req.code:
            raise ValueError("Code content must be provided in code mode.")
        spec = None
        param_obj = None
        model_hash = compute_code_model_hash(req.code, material.id)
        
    t_parse = (time.perf_counter() - t0) * 1000.0
    
    # Check cache
    if model_hash in _CACHE:
        solid, _, _, physics, checks, verts, faces = _CACHE[model_hash]
        warnings = []
    else:
        t_geom_start = time.perf_counter()
        if req.source == "template":
            raw_part = spec.build_func(param_obj)
        else:
            # 1. Compile user code to capture syntax errors with exact line
            try:
                code_obj = compile(req.code, "<user_code>", "exec")
            except SyntaxError as se:
                line_no = se.lineno
                line_text = se.text.strip() if se.text else None
                err = WorkerError(
                    req_id=req.req_id,
                    kind="code_error",
                    message_key=f"SyntaxError: {se.msg} (Satır {line_no})",
                    detail=traceback.format_exc(),
                    line_no=line_no,
                    line_text=line_text,
                    hint="Sözdizimi hatası: Parantez, tırnak veya girintileri kontrol edin."
                )
                raise CodeExecError(err)

            # 2. Execute user code in unified namespace scope (B9)
            import math
            import build123d as bd
            scope: Dict[str, Any] = {
                "__builtins__": __builtins__,
                "build123d": bd,
                "bd": bd,
                "math": math,
            }
            try:
                exec(code_obj, scope, scope)
            except Exception as e:
                tb = sys.exc_info()[2]
                line_no = None
                line_text = None
                for frame, lineno in traceback.walk_tb(tb):
                    if frame.f_code.co_filename == "<user_code>":
                        line_no = lineno
                if line_no is not None and req.code:
                    lines = req.code.splitlines()
                    if 1 <= line_no <= len(lines):
                        line_text = lines[line_no - 1].strip()

                err = WorkerError(
                    req_id=req.req_id,
                    kind="code_error",
                    message_key=f"{type(e).__name__}: {str(e)} (Satır {line_no})",
                    detail=traceback.format_exc(),
                    line_no=line_no,
                    line_text=line_text,
                    hint="Kod çalıştırılırken hata oluştu. Değişkenleri ve build123d API çağrılarını kontrol edin."
                )
                raise CodeExecError(err)

            if "result" in scope:
                raw_part = scope["result"]
            elif "part" in scope:
                raw_part = scope["part"]
            else:
                err = WorkerError(
                    req_id=req.req_id,
                    kind="code_error",
                    message_key="Kod çıktısı bulunamadı: 'result' veya 'part' değişkeni atanmalıdır.",
                    detail="No output variable found in script namespace.",
                    hint="Kodunuzun sonuna 'result = p.part' veya 'result = my_solid' ekleyin."
                )
                raise CodeExecError(err)
                
        solid = validate_solid(raw_part)
        t_geom = (time.perf_counter() - t_geom_start) * 1000.0
        
        # Post-generation geometry sanity warnings
        warnings = []
        if hasattr(raw_part, "solids") and len(raw_part.solids()) > 1:
            warnings.append(f"Model {len(raw_part.solids())} bağımsız ayrık gövdeden oluşuyor.")
            
        try:
            bbox = solid.bounding_box()
            dx, dy, dz = bbox.size.X, bbox.size.Y, bbox.size.Z
            if max(dx, dy, dz) > 5000:
                warnings.append(f"Model boyutu 5000 mm üzerinde ({max(dx, dy, dz):.1f} mm).")
            dims = [d for d in (dx, dy, dz) if d > 1e-3]
            if len(dims) == 3 and (max(dims) / min(dims) > 500):
                warnings.append("Yüksek en-boy oranı (>500:1); et kalınlığı veya ölçek parametrelerini kontrol edin.")
        except Exception:
            pass

        # Physics
        physics = compute_physics(solid, material)
        
        # Engineering checks
        checks = []
        if spec and spec.checks_func:
            checks = spec.checks_func(param_obj, material, physics)
            
        # Tessellation
        tol = 0.05 if req.quality == "export" else 0.15
        verts, faces = tessellate_solid(solid, tolerance=tol)
        if len(faces) > 200_000:
            warnings.append(f"Yoğun ağ üretildi ({len(faces):,} üçgen); önizleme yavaşlayabilir.")
        
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
        warnings=warnings,
        timings_ms={"total": round(t_total, 1), "parse": round(t_parse, 1)}
    )

def process_export(req: ExportRequest) -> ExportResult:
    if req.model_hash not in _CACHE:
        # Rebuild on demand upon cache miss (B18)
        build_req = BuildRequest(
            req_id=f"rebuild_{req.req_id}",
            source=req.source,
            template_id=req.template_id,
            template_version=req.template_version,
            params=req.params,
            code=req.code,
            material_id=req.material_id,
            loads=req.loads,
            quality="export"
        )
        process_build(build_req)
        if req.model_hash not in _CACHE and _CACHE:
            recent_hash = next(reversed(_CACHE.keys()))
            solid, param_obj, material, physics, checks, verts, faces = _CACHE[recent_hash]
        elif req.model_hash in _CACHE:
            solid, param_obj, material, physics, checks, verts, faces = _CACHE[req.model_hash]
        else:
            raise ValueError(f"Failed to rebuild model for export: {req.model_hash}")
    else:
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
        temp_png = out_path.with_suffix(".temp_preview.png")
        render_mesh_to_png(verts, faces, temp_png, image_size=(800, 600))
        params_dict = param_obj.model_dump() if hasattr(param_obj, "model_dump") else (req.params or {})
        
        # Resolve real template name & version (B19)
        reg = TemplateRegistry.get_default_registry()
        tpl_name = "PCAD Model"
        tpl_ver = req.template_version or "1.0.0"
        if req.template_id:
            try:
                spec = reg.get(req.template_id)
                tpl_name = str(spec.name.get("en") if isinstance(spec.name, dict) else spec.name)
                tpl_ver = spec.version
            except Exception:
                tpl_name = req.template_id
        elif req.source == "code":
            tpl_name = "Custom Code Model"
            tpl_ver = "custom"

        generate_datasheet_pdf(
            output_pdf_path=out_path,
            template_name=tpl_name,
            template_version=tpl_ver,
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
    sys.stdout.write(json.dumps({"status": "ready"}) + "\n")
    sys.stdout.flush()

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
                
        except CodeExecError as cee:
            resp = {"status": "error", "error": cee.worker_error.model_dump()}
        except Exception as e:
            trace = traceback.format_exc()
            err_kind = "geometry_invalid" if isinstance(e, GeometryError) or "GeometryError" in type(e).__name__ else "param_invalid"
            payload_dict = data.get("payload", data) if "data" in locals() and isinstance(data, dict) else {}
            req_id_val = payload_dict.get("req_id", "unknown") if isinstance(payload_dict, dict) else "unknown"
            hint = "Geometri kısıtları ihlal edildi veya geçersiz manifold katı oluştu." if err_kind == "geometry_invalid" else "Parametre değerlerini ve sınırlarını kontrol edin."
            err = WorkerError(
                req_id=req_id_val,
                kind=err_kind,
                message_key=str(e),
                detail=trace,
                hint=hint
            )
            resp = {"status": "error", "error": err.model_dump()}
            
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
