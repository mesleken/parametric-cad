"""Deterministic model hashing for cache keys and traceability."""

import json
import hashlib
import sys
from typing import Any, Dict, Optional
import build123d

def get_default_kernel_version() -> str:
    ver = getattr(build123d, "__version__", "0.13.0")
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    return f"build123d-{ver}-py{py_ver}"

def compute_model_hash(
    template_id: str,
    template_version: str,
    params: Dict[str, Any],
    material_id: str,
    loads: Optional[Dict[str, float]] = None,
    kernel_version: Optional[str] = None
) -> str:
    """Computes a canonical SHA-256 hash identifying the exact model configuration."""
    k_ver = kernel_version if kernel_version is not None else get_default_kernel_version()
    canonical_data = {
        "template_id": template_id,
        "template_version": template_version,
        "params": {k: params[k] for k in sorted(params.keys())},
        "material_id": material_id,
        "loads": {k: (loads or {})[k] for k in sorted((loads or {}).keys())},
        "kernel_version": k_ver,
    }
    encoded = json.dumps(canonical_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def compute_code_model_hash(
    code: str,
    material_id: str,
    kernel_version: Optional[str] = None
) -> str:
    """Computes a canonical SHA-256 hash for code mode execution."""
    code_sha = hashlib.sha256(code.strip().encode("utf-8")).hexdigest()
    return compute_model_hash(
        template_id="custom_code",
        template_version="sha256",
        params={"code_sha256": code_sha},
        material_id=material_id,
        kernel_version=kernel_version
    )
