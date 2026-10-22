"""Standard Weld-Neck / Pipe Flange template."""

from typing import Annotated, List
from pydantic import BaseModel, Field, model_validator
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, PhysicsResult, UI, template
from pcad.engineering.flange_checks import check_flange

class FlangeParams(BaseModel):
    outer_dia: Annotated[float, Field(gt=20.0, le=1000.0), UI(label={"en": "Outer Diameter (OD)", "tr": "Dış Çap (OD)"}, unit="mm", group="geometry", step=5.0)] = 120.0
    inner_dia: Annotated[float, Field(gt=5.0, le=800.0), UI(label={"en": "Bore Diameter (ID)", "tr": "İç Delik Çapı (ID)"}, unit="mm", group="geometry", step=5.0)] = 40.0
    flange_thickness: Annotated[float, Field(gt=2.0, le=150.0), UI(label={"en": "Flange Thickness (t)", "tr": "Flanş Kalınlığı (t)"}, unit="mm", group="geometry", step=1.0)] = 16.0
    neck_height: Annotated[float, Field(ge=0.0, le=300.0), UI(label={"en": "Neck Height (h)", "tr": "Boyun Yüksekliği (h)"}, unit="mm", group="geometry", step=5.0)] = 30.0
    neck_outer_dia: Annotated[float, Field(gt=10.0, le=900.0), UI(label={"en": "Neck Outer Dia", "tr": "Boyun Dış Çapı"}, unit="mm", group="geometry", step=2.0)] = 60.0
    pcd: Annotated[float, Field(gt=15.0, le=950.0), UI(label={"en": "Bolt Circle Dia (PCD)", "tr": "Cıvata Dairesi (PCD)"}, unit="mm", group="geometry", step=5.0)] = 90.0
    num_bolts: Annotated[int, Field(ge=3, le=48), UI(label={"en": "Number of Bolts", "tr": "Cıvata Sayısı"}, unit="-", group="geometry", step=1.0)] = 4
    bolt_hole_dia: Annotated[float, Field(gt=2.0, le=60.0), UI(label={"en": "Bolt Hole Dia (d)", "tr": "Cıvata Delik Çapı (d)"}, unit="mm", group="geometry", step=1.0)] = 12.0
    fillet_radius: Annotated[float, Field(ge=0.0, le=30.0), UI(label={"en": "Fillet Radius (R)", "tr": "Pah / Radyus (R)"}, unit="mm", group="geometry", step=0.5)] = 4.0

    @model_validator(mode="after")
    def validate_proportions(self):
        if self.inner_dia >= self.neck_outer_dia:
            raise ValueError("Bore diameter must be less than neck outer diameter.")
        if self.neck_outer_dia >= self.pcd - self.bolt_hole_dia:
            raise ValueError("Neck diameter interferes with bolt circle holes.")
        if self.pcd + self.bolt_hole_dia >= self.outer_dia:
            raise ValueError("Bolt circle holes exceed outer flange boundary.")
        return self

@template(
    id="demo.flange",
    version="1.0.0",
    category="Standard & Piping",
    name={"en": "Weld-Neck Pipe Flange", "tr": "Boyunlu Boru Flanşı"},
    description={
        "en": "Parametric weld-neck flange with circular bolt pattern and hub transition.",
        "tr": "Dairesel cıvata dizilimine ve boyun geçişine sahip parametrik flanş."
    },
    params=FlangeParams,
    default_material="AISI4140"
)
def build(p: FlangeParams):
    from build123d import (
        BuildPart, Cylinder, Circle, Locations, PolarLocations, Mode, fillet, Axis
    )
    
    with BuildPart() as builder:
        # 1. Main flange disk
        Cylinder(radius=p.outer_dia / 2.0, height=p.flange_thickness)
        
        # 2. Hub / neck transition if height > 0
        if p.neck_height > 0 and p.neck_outer_dia > p.inner_dia:
            with Locations((0, 0, p.flange_thickness / 2.0 + p.neck_height / 2.0)):
                Cylinder(radius=p.neck_outer_dia / 2.0, height=p.neck_height)
                
        # 3. Central bore through entire part
        total_h = p.flange_thickness + p.neck_height + 10.0
        with Locations((0, 0, 0)):
            Cylinder(radius=p.inner_dia / 2.0, height=total_h, mode=Mode.SUBTRACT)
            
        # 4. Bolt hole pattern
        with PolarLocations(radius=p.pcd / 2.0, count=p.num_bolts):
            Cylinder(radius=p.bolt_hole_dia / 2.0, height=p.flange_thickness * 2.0, mode=Mode.SUBTRACT)
            
    return builder.part

def checks(p: FlangeParams, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    return check_flange(
        outer_dia=p.outer_dia,
        inner_dia=p.inner_dia,
        pcd=p.pcd,
        num_bolts=p.num_bolts,
        bolt_hole_dia=p.bolt_hole_dia,
        flange_thickness=p.flange_thickness,
        material=material
    )

# Attach checks function to spec
build.checks_func = checks
