"""Template specification, parameter metadata, and result contracts."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from pydantic import BaseModel, Field

from pcad.domain.constraints import ConstraintRule

class MarginStatus(str, Enum):
    POSITIVE = "POSITIVE"
    LOW = "LOW"
    NEGATIVE = "NEGATIVE"

class CheckResult(BaseModel):
    name: str
    status: MarginStatus
    margin_of_safety: float
    applied: float
    allowable: float
    unit: str = "MPa"
    fos: float = 1.5
    rule_ref: str = ""
    message: str = ""

class PhysicsResult(BaseModel):
    volume_mm3: float
    mass_g: float
    surface_area_mm2: float = 0.0
    cog_mm: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    bbox_mm: Tuple[float, float, float, float, float, float] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0) # xmin, ymin, zmin, xmax, ymax, zmax
    inertia_g_mm2: Tuple[float, float, float] = (0.0, 0.0, 0.0) # Ixx, Iyy, Izz

@dataclass
class UI:
    """UI presentation metadata attached via Annotated[type, Field(...), UI(...)]"""
    label: Union[str, Dict[str, str]]
    unit: str = "mm"
    group: str = "geometry"
    step: float = 1.0
    help: Union[str, Dict[str, str]] = ""
    choices: Optional[List[str]] = None

@dataclass
class TemplateSpec:
    id: str
    version: str
    category: str
    name: Union[str, Dict[str, str]]
    description: Union[str, Dict[str, str]]
    param_cls: Type[BaseModel]
    default_material: str
    build_func: Callable[[Any], Any]
    checks_func: Optional[Callable[[Any, Any, PhysicsResult], List[CheckResult]]] = None
    constraints: List[ConstraintRule] = field(default_factory=list)

    def __call__(self, *args, **kwargs):
        return self.build_func(*args, **kwargs)

def template(
    id: str,
    version: str = "1.0.0",
    category: str = "general",
    name: Union[str, Dict[str, str]] = "",
    description: Union[str, Dict[str, str]] = "",
    params: Optional[Type[BaseModel]] = None,
    default_material: str = "Al7075-T6",
    constraints: Optional[List[ConstraintRule]] = None
):
    """Decorator to register a function as a CAD template builder."""
    def decorator(fn: Callable[[Any], Any]) -> TemplateSpec:
        spec = TemplateSpec(
            id=id,
            version=version,
            category=category,
            name=name or id,
            description=description,
            param_cls=params or BaseModel,
            default_material=default_material,
            build_func=fn,
            constraints=constraints or []
        )
        # Store spec on the function object for discovery
        fn._pcad_template_spec = spec
        return spec
    return decorator
