"""Parametric Device Enclosure / Electronics Casing with Internal Standoffs."""

from typing import Annotated, List
from pydantic import BaseModel, Field, model_validator
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, PhysicsResult, UI, template
from pcad.engineering.enclosure_checks import check_enclosure

class EnclosureParams(BaseModel):
    # Overall Dimensions
    length: Annotated[float, Field(gt=20.0, le=500.0), UI(label={"en": "Outer Length (L)", "tr": "Dış Boy (L)"}, unit="mm", group="geometry", step=5.0)] = 110.0
    width: Annotated[float, Field(gt=20.0, le=400.0), UI(label={"en": "Outer Width (W)", "tr": "Dış En (W)"}, unit="mm", group="geometry", step=5.0)] = 75.0
    height: Annotated[float, Field(gt=10.0, le=300.0), UI(label={"en": "Outer Height (H)", "tr": "Dış Yükseklik (H)"}, unit="mm", group="geometry", step=5.0)] = 40.0
    wall_thickness: Annotated[float, Field(gt=1.0, le=25.0), UI(label={"en": "Wall Thickness (t)", "tr": "Et Kalınlığı (t)"}, unit="mm", group="geometry", step=0.5)] = 3.0
    
    # Internal PCB / Standoff Bosses
    standoff_height: Annotated[float, Field(ge=2.0, le=200.0), UI(label={"en": "Standoff Height", "tr": "Yükseltici Ayak Boyu"}, unit="mm", group="standoffs", step=1.0)] = 12.0
    boss_od: Annotated[float, Field(gt=3.0, le=30.0), UI(label={"en": "Boss Outer Dia", "tr": "Ayak Dış Çapı"}, unit="mm", group="standoffs", step=0.5)] = 8.0
    screw_dia: Annotated[float, Field(gt=1.0, le=12.0), UI(label={"en": "Screw Pilot Hole Dia", "tr": "Vida Kılavuz Delik Ø"}, unit="mm", group="standoffs", step=0.5)] = 3.2

    @model_validator(mode="after")
    def validate_enclosure(self):
        if (2.0 * self.wall_thickness) >= self.width or (2.0 * self.wall_thickness) >= self.length:
            raise ValueError("Wall thickness is too large for enclosure outer boundaries.")
        if self.standoff_height >= (self.height - self.wall_thickness):
            raise ValueError("Standoff height exceeds internal box depth.")
        if self.screw_dia >= self.boss_od:
            raise ValueError("Screw pilot hole must be less than boss outer diameter.")
        return self

@template(
    id="mech.enclosure",
    version="1.0.0",
    category="Enclosures & Housings",
    name={"en": "Electronics Device Enclosure", "tr": "Elektronik Cihaz / Modül Kasası"},
    description={
        "en": "Parametric hollow electronics project box with internal PCB mounting standoffs and structural rigidity evaluation.",
        "tr": "Dahili PCB montaj kulelerine ve yapısal rijitlik kontrolüne sahip parametrik cihaz kutusu."
    },
    params=EnclosureParams,
    default_material="Al6061-T6"
)
def build(p: EnclosureParams):
    from build123d import (
        BuildPart, Box, Cylinder, Locations, Mode, fillet, Axis
    )
    
    inner_l = p.length - (2.0 * p.wall_thickness)
    inner_w = p.width - (2.0 * p.wall_thickness)
    inner_h = p.height - p.wall_thickness + 1.0 # open at top
    
    with BuildPart() as builder:
        # 1. Solid Outer Box
        Box(p.length, p.width, p.height)
        
        # 2. Hollow Pocket cavity from top (+Z)
        with Locations((0, 0, (p.wall_thickness / 2.0) + 0.5)):
            Box(inner_l, inner_w, inner_h, mode=Mode.SUBTRACT)
            
        # 3. Add 4 corner standoffs inside the cavity
        # Standoff positions: offset from inside walls
        offset_x = (inner_l / 2.0) - (p.boss_od / 2.0) - 2.0
        offset_y = (inner_w / 2.0) - (p.boss_od / 2.0) - 2.0
        floor_z = -(p.height / 2.0) + p.wall_thickness + (p.standoff_height / 2.0)
        
        corner_locs = [
            (offset_x, offset_y, floor_z),
            (-offset_x, offset_y, floor_z),
            (offset_x, -offset_y, floor_z),
            (-offset_x, -offset_y, floor_z),
        ]
        
        with Locations(corner_locs):
            Cylinder(radius=p.boss_od / 2.0, height=p.standoff_height, mode=Mode.ADD)
            Cylinder(radius=p.screw_dia / 2.0, height=p.standoff_height + 2.0, mode=Mode.SUBTRACT)

    return builder.part

build.checks_func = check_enclosure
