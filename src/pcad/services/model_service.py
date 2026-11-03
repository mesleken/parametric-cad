"""Unified Headless Model Service (D5, D7).

Centralizes the build -> validate -> physics -> checks -> hash pipeline.
Used by Worker, CLI, and Batch service.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import time

from build123d import Solid
from pcad.domain.hashing import compute_model_hash, compute_code_model_hash
from pcad.domain.materials import Material, MaterialDB
from pcad.domain.template import CheckResult, PhysicsResult, TemplateSpec
from pcad.kernel.validate import validate_solid
from pcad.kernel.physics import compute_physics
from pcad.templates.registry import TemplateRegistry

@dataclass
class ModelRequest:
    source: str = "template"  # "template" or "code"
    template_id: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    material_id: str = "Al7075-T6"
    loads: Dict[str, float] = field(default_factory=dict)
    code: Optional[str] = None

@dataclass
class ModelResponse:
    solid: Solid
    spec: Optional[TemplateSpec]
    param_obj: Any
    material: Material
    physics: PhysicsResult
    checks: List[CheckResult]
    model_hash: str
    build_time_ms: float
    warnings: List[str] = field(default_factory=list)

class ModelService:
    def __init__(self, registry: Optional[TemplateRegistry] = None, mat_db: Optional[MaterialDB] = None):
        self.registry = registry or TemplateRegistry.get_default_registry()
        self.mat_db = mat_db or MaterialDB.get_default_db()

    def generate(self, req: ModelRequest) -> ModelResponse:
        t0 = time.perf_counter()
        material = self.mat_db.get(req.material_id)

        if req.source == "template":
            if not req.template_id:
                raise ValueError("Template ID must be specified for template build.")
            spec = self.registry.get(req.template_id)
            param_cls = spec.param_cls
            param_obj = param_cls(**req.params)
            
            raw_part = spec.build_func(param_obj)
            solid = validate_solid(raw_part)
            physics = compute_physics(solid, material)
            
            checks = []
            if spec.checks_func:
                checks = spec.checks_func(param_obj, material, physics)
                
            model_hash = compute_model_hash(
                template_id=spec.id,
                template_version=spec.version,
                params=param_obj.model_dump(),
                material_id=material.id,
                loads=req.loads
            )
        elif req.source == "code":
            if not req.code:
                raise ValueError("Code content must be provided in code mode.")
            spec = None
            param_obj = None
            
            import math
            import build123d as bd
            scope: Dict[str, Any] = {
                "__builtins__": __builtins__,
                "build123d": bd,
                "bd": bd,
                "math": math,
            }
            code_obj = compile(req.code, "<user_code>", "exec")
            exec(code_obj, scope, scope)
            
            if "result" in scope:
                raw_part = scope["result"]
            elif "part" in scope:
                raw_part = scope["part"]
            else:
                raise ValueError("Code mode script must define 'result' or 'part' Solid variable.")
                
            solid = validate_solid(raw_part)
            physics = compute_physics(solid, material)
            checks = []
            model_hash = compute_code_model_hash(req.code, material.id)
        else:
            raise ValueError(f"Unknown source kind: {req.source}")

        dur = (time.perf_counter() - t0) * 1000.0
        return ModelResponse(
            solid=solid,
            spec=spec,
            param_obj=param_obj,
            material=material,
            physics=physics,
            checks=checks,
            model_hash=model_hash,
            build_time_ms=round(dur, 2)
        )
