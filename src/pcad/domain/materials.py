"""Material definitions, database loader, and lookup interface."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Material(BaseModel):
    id: str
    name: str
    category: str = "General"
    density_g_cm3: float = Field(gt=0, description="Density in g/cm3")
    yield_strength_mpa: float = Field(gt=0, description="Tensile Yield Strength (Rp0.2) in MPa")
    ultimate_strength_mpa: float = Field(gt=0, description="Ultimate Tensile Strength (Rm) in MPa")
    shear_strength_mpa: float = Field(gt=0, description="Allowable or Ultimate Shear Strength in MPa")
    bearing_yield_mpa: Optional[float] = Field(default=None, description="Bearing Yield Strength in MPa")
    bearing_ult_mpa: Optional[float] = Field(default=None, description="Bearing Ultimate Strength in MPa")
    source: str = "Reference Handbook"
    typical: bool = True

class MaterialDB:
    _instance: Optional["MaterialDB"] = None
    _materials: Dict[str, Material] = {}

    def __init__(self, data_file: Optional[Path] = None):
        self._materials = {}
        target_path = data_file or (Path(__file__).parent / "data" / "materials.json")
        if not target_path.exists():
            raise FileNotFoundError(f"Material database file not found: {target_path}")
        with open(target_path, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
            for item in raw_list:
                mat = Material(**item)
                self._materials[mat.id] = mat

    @classmethod
    def get_default_db(cls) -> "MaterialDB":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def list_materials(self) -> List[Material]:
        return list(self._materials.values())

    def get(self, material_id: str) -> Material:
        if material_id in self._materials:
            return self._materials[material_id]
        raise KeyError(
            f"Unknown material ID: '{material_id}'. "
            f"Available materials: {list(self._materials.keys())}"
        )
