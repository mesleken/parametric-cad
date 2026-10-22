"""Deterministic model hashing for cache keys and traceability."""

import json
import hashlib
from typing import Any, Dict

def compute_model_hash(
    template_id: str,
    template_version: str,
    params: Dict[str, Any],
    material_id: str,
    loads: Dict[str, float] = None,
    kernel_version: str = "build123d-0.13.0"
) -> str:
    """Computes a canonical SHA-256 hash identifying the exact model configuration."""
    canonical_data = {
        "template_id": template_id,
        "template_version": template_version,
        "params": {k: params[k] for k in sorted(params.keys())},
        "material_id": material_id,
        "loads": {k: (loads or {})[k] for k in sorted((loads or {}).keys())},
        "kernel_version": kernel_version,
    }
    encoded = json.dumps(canonical_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
