"""Stiffened L-Bracket / Gusseted Angle Bracket template."""

from typing import Annotated, List
from pydantic import BaseModel, Field, model_validator
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, PhysicsResult, UI, template
from pcad.engineering.bending import check_bracket

class BracketParams(BaseModel):
    length_base: Annotated[float, Field(gt=15.0, le=400.0), UI(label={"en": "Base Leg Length", "tr": "Taban Kol Boyu"}, unit="mm", group="geometry", step=5.0)] = 80.0
    length_upright: Annotated[float, Field(gt=15.0, le=400.0), UI(label={"en": "Upright Leg Length", "tr": "Dikey Kol Boyu"}, unit="mm", group="geometry", step=5.0)] = 90.0
    width: Annotated[float, Field(gt=10.0, le=300.0), UI(label={"en": "Bracket Width", "tr": "Braket Genişliği"}, unit="mm", group="geometry", step=5.0)] = 50.0
    thickness: Annotated[float, Field(gt=1.5, le=40.0), UI(label={"en": "Plate Thickness (t)", "tr": "Et Kalınlığı (t)"}, unit="mm", group="geometry", step=0.5)] = 5.0
    inner_radius: Annotated[float, Field(ge=0.5, le=30.0), UI(label={"en": "Inner Bend Radius", "tr": "İç Büküm Radyusu"}, unit="mm", group="geometry", step=0.5)] = 7.5
    gusset_count: Annotated[int, Field(ge=0, le=5), UI(label={"en": "Gusset Rib Count", "tr": "Kaburga Sayısı"}, unit="-", group="geometry", step=1.0)] = 1
    gusset_thickness: Annotated[float, Field(gt=1.0, le=30.0), UI(label={"en": "Gusset Thickness", "tr": "Kaburga Kalınlığı"}, unit="mm", group="geometry", step=0.5)] = 4.0
    
    # Loads
    tip_load_n: Annotated[float, Field(ge=0.0, le=1e6), UI(label={"en": "Tip Load (F)", "tr": "Uç Nokta Yükü (F)"}, unit="N", group="loads", step=100.0)] = 600.0
    fos: Annotated[float, Field(gt=1.0, le=5.0), UI(label={"en": "Factor of Safety", "tr": "Emniyet Katsayısı"}, unit="-", group="advanced", step=0.1)] = 1.5

    @model_validator(mode="after")
    def validate_bracket(self):
        if self.thickness >= min(self.length_base, self.length_upright):
            raise ValueError("Thickness cannot exceed leg lengths.")
        return self

@template(
    id="aero.bracket",
    version="1.0.0",
    category="Aerospace & Structural",
    name={"en": "Gusseted L-Bracket", "tr": "Takviyeli L-Braket"},
    description={
        "en": "Structural angle bracket with triangular stiffening gusset and bending margin checks.",
        "tr": "Üçgen takviye kaburgasına ve eğilme marjı kontrolüne sahip yapısal L-braket."
    },
    params=BracketParams,
    default_material="Al7075-T6"
)
def build(p: BracketParams):
    from build123d import (
        BuildPart, Box, Wedge, Locations, Mode, Align
    )
    
    with BuildPart() as builder:
        # 1. Base horizontal plate
        Box(p.length_base, p.width, p.thickness, align=(Align.MIN, Align.CENTER, Align.MIN))
        
        # 2. Upright vertical plate
        Box(p.thickness, p.width, p.length_upright, align=(Align.MIN, Align.CENTER, Align.MIN))
        
        # 3. Gusset rib(s)
        if p.gusset_count > 0 and p.gusset_thickness > 0:
            gusset_dx = p.length_base * 0.65
            gusset_dz = p.length_upright * 0.65
            
            from build123d import BuildSketch, Polygon, extrude, Plane
            with BuildSketch(Plane.XZ) as sk:
                Polygon([
                    (p.thickness, p.thickness),
                    (gusset_dx, p.thickness),
                    (p.thickness, gusset_dz)
                ])
            # Extrude in Y centered
            extrude(amount=p.gusset_thickness / 2.0, both=True)
            
    return builder.part

def checks(p: BracketParams, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    return check_bracket(
        length_mm=p.length_upright,
        width_mm=p.width,
        thickness_mm=p.thickness,
        inner_radius_mm=p.inner_radius,
        load_n=p.tip_load_n,
        material=material,
        gusset_count=p.gusset_count,
        gusset_thickness_mm=p.gusset_thickness,
        fos=p.fos
    )

build.checks_func = checks
