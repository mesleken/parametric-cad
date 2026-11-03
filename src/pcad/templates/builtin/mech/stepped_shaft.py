"""Stepped Transmission Shaft with Keyway and Shoulder Fillets."""

from typing import Annotated, List
from pydantic import BaseModel, Field, model_validator
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, PhysicsResult, UI, template
from pcad.engineering.shaft_checks import check_stepped_shaft

class SteppedShaftParams(BaseModel):
    # Journal 1 (Drive end)
    d1: Annotated[float, Field(gt=5.0, le=200.0), UI(label={"en": "Journal 1 Dia (d1)", "tr": "Giriş Çapı (d1)"}, unit="mm", group="geometry", step=2.0)] = 25.0
    l1: Annotated[float, Field(gt=10.0, le=400.0), UI(label={"en": "Journal 1 Length (l1)", "tr": "Giriş Boyu (l1)"}, unit="mm", group="geometry", step=5.0)] = 45.0
    
    # Journal 2 (Shoulder / Bearing seat)
    d2: Annotated[float, Field(gt=8.0, le=250.0), UI(label={"en": "Shoulder Dia (d2)", "tr": "Fatura Çapı (d2)"}, unit="mm", group="geometry", step=2.0)] = 35.0
    l2: Annotated[float, Field(gt=10.0, le=500.0), UI(label={"en": "Shoulder Length (l2)", "tr": "Fatura Boyu (l2)"}, unit="mm", group="geometry", step=5.0)] = 60.0
    
    # Journal 3 (Output end)
    d3: Annotated[float, Field(gt=5.0, le=200.0), UI(label={"en": "Journal 3 Dia (d3)", "tr": "Çıkış Çapı (d3)"}, unit="mm", group="geometry", step=2.0)] = 20.0
    l3: Annotated[float, Field(gt=10.0, le=400.0), UI(label={"en": "Journal 3 Length (l3)", "tr": "Çıkış Boyu (l3)"}, unit="mm", group="geometry", step=5.0)] = 35.0
    
    # Keyway & Fillets
    has_keyway: Annotated[bool, UI(label={"en": "Include Drive Keyway", "tr": "Kama Kanalı Ekle"}, group="features")] = True
    kw_length: Annotated[float, Field(gt=5.0, le=200.0), UI(label={"en": "Keyway Length", "tr": "Kama Boyu"}, unit="mm", group="features", step=5.0)] = 28.0
    kw_width: Annotated[float, Field(gt=1.0, le=30.0), UI(label={"en": "Keyway Width", "tr": "Kama Genişliği"}, unit="mm", group="features", step=1.0)] = 8.0
    kw_depth: Annotated[float, Field(gt=0.5, le=15.0), UI(label={"en": "Keyway Depth", "tr": "Kama Derinliği"}, unit="mm", group="features", step=0.5)] = 4.0
    r_fillet: Annotated[float, Field(ge=0.5, le=20.0), UI(label={"en": "Shoulder Fillet Radius", "tr": "Geçiş Radyusu (r)"}, unit="mm", group="features", step=0.5)] = 2.0
    
    # Loads
    torque_nm: Annotated[float, Field(ge=0.0, le=50000.0), UI(label={"en": "Transmitted Torque", "tr": "İletilen Tork"}, unit="N·m", group="loads", step=25.0)] = 150.0
    fos: Annotated[float, Field(gt=1.0, le=5.0), UI(label={"en": "Factor of Safety", "tr": "Emniyet Katsayısı"}, unit="-", group="advanced", step=0.1)] = 1.5

    @model_validator(mode="after")
    def validate_shaft(self):
        if self.d2 <= self.d1 or self.d2 <= self.d3:
            raise ValueError("Central shoulder diameter (d2) must be greater than both journal diameters (d1, d3).")
        if self.r_fillet >= (self.d2 - self.d1) / 2.0 or self.r_fillet >= (self.d2 - self.d3) / 2.0:
            raise ValueError("Fillet radius exceeds shoulder step height.")
        if self.has_keyway:
            if self.kw_length >= self.l1:
                raise ValueError("Keyway length exceeds journal 1 length.")
            if self.kw_width >= self.d1:
                raise ValueError("Keyway width exceeds shaft diameter.")
            if self.kw_depth >= self.d1 / 2.0:
                raise ValueError("Keyway depth exceeds shaft radius.")
        return self

@template(
    id="mech.stepped_shaft",
    version="1.0.0",
    category="Mechanical & Drives",
    name={"en": "Stepped Transmission Shaft", "tr": "Kademeli Şanzıman / İletim Mili"},
    description={
        "en": "Multi-step power transmission shaft with DIN 6885 keyway and shoulder stress concentration analysis.",
        "tr": "DIN 6885 kama kanallı ve fatura gerilme yığılması analizli kademeli güç iletim mili."
    },
    params=SteppedShaftParams,
    default_material="AISI4140"
)
def build(p: SteppedShaftParams):
    from build123d import (
        BuildPart, Cylinder, Box, Locations, Mode, Align, GeomType, fillet
    )
    
    with BuildPart() as builder:
        # 1. Journal 1 (Z: 0 to l1)
        Cylinder(radius=p.d1 / 2.0, height=p.l1, align=(Align.CENTER, Align.CENTER, Align.MIN))
        
        # 2. Shoulder 2 (Z: l1 to l1 + l2)
        with Locations((0, 0, p.l1)):
            Cylinder(radius=p.d2 / 2.0, height=p.l2, align=(Align.CENTER, Align.CENTER, Align.MIN))
            
        # 3. Journal 3 (Z: l1 + l2 to l1 + l2 + l3)
        with Locations((0, 0, p.l1 + p.l2)):
            Cylinder(radius=p.d3 / 2.0, height=p.l3, align=(Align.CENTER, Align.CENTER, Align.MIN))
            
        # 4. Shoulder transition fillets
        if p.r_fillet > 0:
            shoulder_edges = builder.edges().filter_by(GeomType.CIRCLE).filter_by(
                lambda e: (abs(e.center().Z - p.l1) < 1e-3 and abs(e.radius - p.d1 / 2.0) < 1e-3) or
                          (abs(e.center().Z - (p.l1 + p.l2)) < 1e-3 and abs(e.radius - p.d3 / 2.0) < 1e-3)
            )
            if shoulder_edges:
                fillet(shoulder_edges, radius=p.r_fillet)

        # 5. Cut DIN 6885 Keyway centered on Journal 1 (strictly within 0 to l1)
        if p.has_keyway:
            kw_z = p.l1 / 2.0
            kw_y = (p.d1 / 2.0) - (p.kw_depth / 2.0)
            with Locations((0, kw_y, kw_z)):
                Box(p.kw_width, p.kw_depth, p.kw_length, mode=Mode.SUBTRACT)

    return builder.part

build.checks_func = check_stepped_shaft
