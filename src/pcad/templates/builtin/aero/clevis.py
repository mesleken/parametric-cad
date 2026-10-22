"""U-Clevis fitting with pin and cylindrical mounting shank."""

from typing import Annotated, List
from pydantic import BaseModel, Field, model_validator
from pcad.domain.materials import Material, MaterialDB
from pcad.domain.template import CheckResult, PhysicsResult, UI, template
from pcad.engineering.clevis_pin import check_clevis

class ClevisParams(BaseModel):
    gap: Annotated[float, Field(gt=4.0, le=200.0), UI(label={"en": "Clevis Gap (g)", "tr": "Çatal Açıklığı (g)"}, unit="mm", group="geometry", step=1.0)] = 20.0
    t_prong: Annotated[float, Field(gt=2.0, le=80.0), UI(label={"en": "Prong Thickness (t)", "tr": "Kulak Kalınlığı (t)"}, unit="mm", group="geometry", step=1.0)] = 8.0
    w_prong: Annotated[float, Field(gt=10.0, le=250.0), UI(label={"en": "Prong Width (W)", "tr": "Kulak Genişliği (W)"}, unit="mm", group="geometry", step=2.0)] = 40.0
    d_pin: Annotated[float, Field(gt=3.0, le=100.0), UI(label={"en": "Pin Diameter (D)", "tr": "Pim Çapı (D)"}, unit="mm", group="geometry", step=1.0)] = 12.0
    e_hole: Annotated[float, Field(gt=5.0, le=200.0), UI(label={"en": "Hole Center Distance", "tr": "Delik Merkez Mesafesi"}, unit="mm", group="geometry", step=1.0)] = 22.0
    shank_dia: Annotated[float, Field(gt=5.0, le=200.0), UI(label={"en": "Shank Diameter", "tr": "Gövde Şaft Çapı"}, unit="mm", group="geometry", step=2.0)] = 28.0
    shank_length: Annotated[float, Field(gt=5.0, le=300.0), UI(label={"en": "Shank Length", "tr": "Gövde Şaft Boyu"}, unit="mm", group="geometry", step=5.0)] = 35.0
    
    # Loads
    load_f_n: Annotated[float, Field(ge=0.0, le=1e7), UI(label={"en": "Axial Limit Load (F)", "tr": "Eksenel Limit Yük (F)"}, unit="N", group="loads", step=1000.0)] = 15000.0
    fos: Annotated[float, Field(gt=1.0, le=5.0), UI(label={"en": "Factor of Safety", "tr": "Emniyet Katsayısı"}, unit="-", group="advanced", step=0.1)] = 1.5

    @model_validator(mode="after")
    def validate_clevis(self):
        if self.d_pin >= self.w_prong:
            raise ValueError("Pin diameter must be less than prong width.")
        if self.e_hole <= (self.d_pin / 2.0):
            raise ValueError("Hole center distance must be greater than D/2.")
        return self

@template(
    id="aero.clevis",
    version="1.0.0",
    category="Aerospace & Structural",
    name={"en": "Aerospace U-Clevis", "tr": "Havacılık Çatal Bağlantısı (Clevis)"},
    description={
        "en": "Dual-ear clevis fitting with pin shear and flexure stress verification.",
        "tr": "Pim kesme ve eğilme kontrolüne sahip çift kulaklı havacılık çatal bağlantısı."
    },
    params=ClevisParams,
    default_material="Al7075-T6"
)
def build(p: ClevisParams):
    from build123d import (
        BuildPart, Box, Cylinder, Locations, Mode, Align
    )
    
    total_w = p.gap + (2.0 * p.t_prong)
    
    with BuildPart() as builder:
        # 1. Base shank
        Cylinder(radius=p.shank_dia / 2.0, height=p.shank_length, align=(Align.CENTER, Align.CENTER, Align.MAX))
        
        # 2. Main clevis head block
        with Locations((0, 0, 0)):
            Box(total_w, p.w_prong, p.e_hole, align=(Align.CENTER, Align.CENTER, Align.MIN))
            # Rounded prong tips
            with Locations((0, 0, p.e_hole)):
                Cylinder(radius=p.w_prong / 2.0, height=total_w, rotation=(0, 90, 0))
                # Pin through hole across both prongs
                Cylinder(radius=p.d_pin / 2.0, height=total_w * 2.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
                
        # 3. Cut central gap slot
        slot_height = p.e_hole + (p.w_prong / 2.0) + 5.0
        with Locations((0, 0, 0)):
            Box(p.gap, p.w_prong * 2.0, slot_height * 2.0, align=(Align.CENTER, Align.CENTER, Align.CENTER), mode=Mode.SUBTRACT)
            
    return builder.part

def checks(p: ClevisParams, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    # Use 4140 high strength steel pin as default pin partner
    pin_mat = MaterialDB.get_default_db().get("AISI4140")
    return check_clevis(
        gap=p.gap,
        t_prong=p.t_prong,
        D_pin=p.d_pin,
        W_prong=p.w_prong,
        F_axial_N=p.load_f_n,
        material=material,
        pin_material=pin_mat,
        fos=p.fos
    )

build.checks_func = checks
