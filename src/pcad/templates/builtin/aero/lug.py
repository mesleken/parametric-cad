"""Aerospace Attachment Lug (Pimli Bağlantı Kulağı) Template."""

from typing import Annotated, List
from pydantic import BaseModel, Field, model_validator
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, PhysicsResult, UI, template
from pcad.engineering.lug import check_lug

class LugParams(BaseModel):
    # Geometry
    W: Annotated[float, Field(gt=10.0, le=300.0), UI(label={"en": "Lug Width (W)", "tr": "Kulak Genişliği (W)"}, unit="mm", group="geometry", step=2.0)] = 40.0
    D: Annotated[float, Field(gt=3.0, le=100.0), UI(label={"en": "Pin Hole Dia (D)", "tr": "Pim Deliği Çapı (D)"}, unit="mm", group="geometry", step=1.0)] = 12.0
    e: Annotated[float, Field(gt=5.0, le=200.0), UI(label={"en": "Edge Distance (e)", "tr": "Kenar Mesafesi (e)"}, unit="mm", group="geometry", step=1.0)] = 24.0
    t: Annotated[float, Field(gt=2.0, le=60.0), UI(label={"en": "Lug Thickness (t)", "tr": "Kulak Kalınlığı (t)"}, unit="mm", group="geometry", step=1.0)] = 8.0
    stem_height: Annotated[float, Field(gt=10.0, le=400.0), UI(label={"en": "Stem Height", "tr": "Gövde Yüksekliği"}, unit="mm", group="geometry", step=5.0)] = 30.0
    
    # Base Mounting Plate
    base_length: Annotated[float, Field(gt=10.0, le=400.0), UI(label={"en": "Base Length", "tr": "Taban Boyu"}, unit="mm", group="geometry", step=5.0)] = 60.0
    base_width: Annotated[float, Field(gt=10.0, le=300.0), UI(label={"en": "Base Width", "tr": "Taban Eni"}, unit="mm", group="geometry", step=5.0)] = 50.0
    base_thickness: Annotated[float, Field(gt=2.0, le=50.0), UI(label={"en": "Base Thickness", "tr": "Taban Kalınlığı"}, unit="mm", group="geometry", step=1.0)] = 10.0
    mount_hole_dia: Annotated[float, Field(ge=0.0, le=30.0), UI(label={"en": "Base Mount Hole Ø", "tr": "Taban Montaj Delik Ø"}, unit="mm", group="geometry", step=1.0)] = 6.0
    
    # Design Loads & Advanced Factors
    load_f_n: Annotated[float, Field(ge=0.0, le=1e7), UI(label={"en": "Axial Limit Load (F)", "tr": "Eksenel Limit Yük (F)"}, unit="N", group="loads", step=1000.0)] = 12000.0
    fos: Annotated[float, Field(gt=1.0, le=5.0), UI(label={"en": "Factor of Safety (FoS)", "tr": "Emniyet Katsayısı (FoS)"}, unit="-", group="advanced", step=0.1)] = 1.5
    k_tu: Annotated[float, Field(gt=0.2, le=1.2), UI(label={"en": "Net-Section Factor (Ktu)", "tr": "Net Kesit Verim Faktörü (Ktu)"}, unit="-", group="advanced", step=0.05, help={"en": "From Bruhn D1.2 / MMPDS curves. 1.0 is NOT conservative for high-strength alloys.", "tr": "Bruhn D1.2 eğrilerinden girilmelidir. 1.0 muhafazakâr değildir."})] = 1.0

    @model_validator(mode="after")
    def validate_lug_proportions(self):
        if self.D >= self.W:
            raise ValueError("Pin hole diameter (D) must be less than lug width (W).")
        if self.e <= (self.D / 2.0):
            raise ValueError("Hole center-to-edge distance (e) must be greater than D/2.")
        if self.t > self.base_length:
            raise ValueError("Lug thickness (t) exceeds base mounting plate length.")
        if self.W > self.base_width:
            raise ValueError("Lug width (W) exceeds base mounting plate width.")
        return self

@template(
    id="aero.lug",
    version="1.0.0",
    category="Aerospace & Structural",
    name={"en": "Aerospace Attachment Lug", "tr": "Havacılık Bağlantı Kulağı (Lug)"},
    description={
        "en": "Single-ear attachment lug with mounting flange and Bruhn stress analysis.",
        "tr": "Montaj flanşı ve Bruhn mukavemet marjı analizli havacılık bağlantı kulağı."
    },
    params=LugParams,
    default_material="Al7075-T6"
)
def build(p: LugParams):
    from build123d import (
        BuildPart, Box, Cylinder, Locations, GridLocations, Mode, Align
    )
    
    with BuildPart() as builder:
        # 1. Base mounting plate
        Box(p.base_length, p.base_width, p.base_thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
        
        # 2. Base bolt mounting holes if specified
        if p.mount_hole_dia > 0 and p.base_length > 20 and p.base_width > 20:
            pitch_x = p.base_length * 0.65
            pitch_y = p.base_width * 0.65
            with GridLocations(pitch_x, pitch_y, 2, 2):
                Cylinder(radius=p.mount_hole_dia / 2.0, height=p.base_thickness * 2.0, mode=Mode.SUBTRACT)
                
        # 3. Upright stem up to hole center
        h_hole = p.base_thickness + p.stem_height
        with Locations((0, 0, p.base_thickness)):
            Box(p.t, p.W, p.stem_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
            
        # 4. Lug head above hole center
        # Tip distance from hole center must be exactly e
        if p.e >= (p.W / 2.0):
            extension = p.e - (p.W / 2.0)
            if extension > 0:
                with Locations((0, 0, h_hole)):
                    Box(p.t, p.W, extension, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with Locations((0, 0, h_hole + extension)):
                Cylinder(radius=p.W / 2.0, height=p.t, rotation=(0, 90, 0))
        else:
            with Locations((0, 0, h_hole)):
                Cylinder(radius=p.e, height=p.t, rotation=(0, 90, 0))
                Box(p.t, p.W, p.e, align=(Align.CENTER, Align.CENTER, Align.MIN))
                
        # 5. Pin hole at h_hole
        with Locations((0, 0, h_hole)):
            Cylinder(radius=p.D / 2.0, height=p.t * 2.5, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
                
    return builder.part

def checks(p: LugParams, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    return check_lug(
        W=p.W,
        D=p.D,
        e=p.e,
        t=p.t,
        F_axial_N=p.load_f_n,
        material=material,
        K_tu=p.k_tu,
        fos=p.fos
    )

build.checks_func = checks
