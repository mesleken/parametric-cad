"""Parametric Involute Spur Gear with Hub and Shaft Bore."""

import math
from typing import Annotated, List
from pydantic import BaseModel, Field, model_validator
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, PhysicsResult, UI, template
from pcad.engineering.gear_checks import check_spur_gear

class SpurGearParams(BaseModel):
    module: Annotated[float, Field(gt=0.5, le=20.0), UI(label={"en": "Module (m)", "tr": "Modül (m)"}, unit="mm", group="gear_teeth", step=0.5)] = 2.5
    num_teeth: Annotated[int, Field(ge=10, le=120), UI(label={"en": "Number of Teeth (z)", "tr": "Diş Sayısı (z)"}, unit="-", group="gear_teeth", step=1.0)] = 24
    face_width: Annotated[float, Field(gt=2.0, le=150.0), UI(label={"en": "Face Width (b)", "tr": "Diş Genişliği (b)"}, unit="mm", group="gear_teeth", step=2.0)] = 20.0
    pressure_angle: Annotated[float, Field(ge=14.5, le=25.0), UI(label={"en": "Pressure Angle (α)", "tr": "Kavrama Açısı (α)"}, unit="deg", group="gear_teeth", step=0.5)] = 20.0
    profile_shift: Annotated[float, Field(ge=-0.5, le=0.6), UI(label={"en": "Profile Shift (x)", "tr": "Profil Kaydırma (x)"}, unit="-", group="gear_teeth", step=0.05, help={"en": "ISO 53 addendum modification factor", "tr": "ISO 53 profil kaydırma katsayısı"})] = 0.0
    
    # Hub & Bore
    bore_dia: Annotated[float, Field(gt=3.0, le=100.0), UI(label={"en": "Shaft Bore Dia (d_bore)", "tr": "Mil Delik Çapı (d_bore)"}, unit="mm", group="hub", step=1.0)] = 16.0
    hub_dia: Annotated[float, Field(gt=5.0, le=150.0), UI(label={"en": "Hub Outer Dia", "tr": "Göbek Dış Çapı"}, unit="mm", group="hub", step=2.0)] = 32.0
    hub_length: Annotated[float, Field(ge=0.0, le=100.0), UI(label={"en": "Hub Extension Length", "tr": "Göbek Uzantı Boyu"}, unit="mm", group="hub", step=2.0)] = 10.0
    keyway_enabled: Annotated[bool, UI(label={"en": "Hub Keyway (DIN 6885)", "tr": "Göbek Kama Kanalı (DIN 6885)"}, unit="-", group="hub")] = False
    
    # Loads & Transmission
    torque_nm: Annotated[float, Field(ge=0.0, le=10000.0), UI(label={"en": "Operating Torque", "tr": "Çalışma Torku"}, unit="N·m", group="loads", step=5.0)] = 25.0
    gear_ratio: Annotated[float, Field(gt=0.1, le=10.0), UI(label={"en": "Mating Gear Ratio (u)", "tr": "Karşı Dişli Çevrim Oranı (u)"}, unit="-", group="loads", step=0.1)] = 1.0
    fos: Annotated[float, Field(gt=1.0, le=5.0), UI(label={"en": "Factor of Safety", "tr": "Emniyet Katsayısı"}, unit="-", group="advanced", step=0.1)] = 1.5

    @model_validator(mode="after")
    def validate_gear(self):
        pitch_dia = self.module * self.num_teeth
        dedendum = (1.25 - self.profile_shift) * self.module
        root_dia = pitch_dia - (2.0 * dedendum)
        
        if self.hub_dia >= root_dia:
            raise ValueError(f"Hub diameter ({self.hub_dia} mm) interferes with tooth root circle ({root_dia:.1f} mm).")
        if self.bore_dia >= self.hub_dia - (2.0 * self.module):
            raise ValueError("Shaft bore leaves insufficient hub wall thickness.")
        return self

@template(
    id="mech.spur_gear",
    version="1.0.0",
    category="Mechanical & Drives",
    name={"en": "Involute Spur Gear", "tr": "Düz Alın Dişlisi"},
    description={
        "en": "True involute tooth profile spur gear with ISO 53 profile shift, DIN 6885 hub keyway, and AGMA/ISO capacity checks.",
        "tr": "ISO 53 profil kaydırmalı, DIN 6885 kama kanallı ve AGMA/ISO kontrol modüllü düz alın dişlisi."
    },
    params=SpurGearParams,
    default_material="AISI4140"
)
def build(p: SpurGearParams):
    import build123d as bd
    
    m = p.module
    z = p.num_teeth
    x = p.profile_shift
    alpha = math.radians(p.pressure_angle)
    rp = (m * z) / 2.0
    rb = rp * math.cos(alpha)
    ra = rp + (1.0 + x) * m
    rf = rp - (1.25 - x) * m
    
    def inv(a: float) -> float:
        return math.tan(a) - a

    inv_alpha = inv(alpha)
    # Tooth arc thickness on pitch circle with profile shift x
    sp = m * ((math.pi / 2.0) + (2.0 * x * math.tan(alpha)))
    half_thick_angle = sp / (2.0 * rp)
    pitch_angle = (2.0 * math.pi) / z

    def flank_pt(r: float, sign: float = 1.0):
        r_clamped = max(r, rb)
        cos_ar = min(1.0, rb / r_clamped)
        ar = math.acos(cos_ar)
        th = sign * (half_thick_angle + inv_alpha - inv(ar))
        return (r * math.cos(th), r * math.sin(th))

    # Dense 15-point involute flank points
    all_pts = []
    for k in range(z):
        phi = k * pitch_angle
        cos_phi = math.cos(phi)
        sin_phi = math.sin(phi)
        
        def rot(pt):
            x_pt, y_pt = pt
            return (x_pt * cos_phi - y_pt * sin_phi, x_pt * sin_phi + y_pt * cos_phi)
            
        tooth_pts = []
        # Root trough left
        tooth_pts.append(rot((rf * math.cos(-pitch_angle / 2.0), rf * math.sin(-pitch_angle / 2.0))))
        # Left involute flank (from root to tip, 15 points)
        for s in range(15):
            r = rf + (ra - rf) * (s / 14.0)
            tooth_pts.append(rot(flank_pt(r, -1.0)))
        # Right involute flank (from tip to root, 15 points)
        for s in range(15):
            r = ra - (ra - rf) * (s / 14.0)
            tooth_pts.append(rot(flank_pt(r, 1.0)))
            
        all_pts.extend(tooth_pts)

    with bd.BuildPart() as builder:
        # 1. Extrude true involute gear body
        with bd.BuildSketch():
            bd.Polygon(all_pts)
        bd.extrude(amount=p.face_width)
        
        # 2. Add hub extension if requested
        if p.hub_length > 0.0:
            with bd.Locations((0, 0, p.face_width)):
                bd.Cylinder(radius=p.hub_dia / 2.0, height=p.hub_length, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN), mode=bd.Mode.ADD)
                
        # 3. Central bore through both gear and hub
        total_len = p.face_width + p.hub_length + 10.0
        r_bore = p.bore_dia / 2.0
        with bd.Locations((0, 0, -5.0)):
            bd.Cylinder(radius=r_bore, height=total_len, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN), mode=bd.Mode.SUBTRACT)

        # 4. Standard DIN 6885-1 hub keyway if enabled
        if p.keyway_enabled:
            # DIN 6885-1 keyway dimensions
            d = p.bore_dia
            if d <= 12:
                b_key, t2 = 4.0, 1.8
            elif d <= 17:
                b_key, t2 = 5.0, 2.3
            elif d <= 22:
                b_key, t2 = 6.0, 2.8
            elif d <= 30:
                b_key, t2 = 8.0, 3.3
            elif d <= 38:
                b_key, t2 = 10.0, 3.3
            elif d <= 44:
                b_key, t2 = 12.0, 3.3
            else:
                b_key, t2 = 14.0, 3.8
            
            with bd.Locations((0, r_bore, (p.face_width + p.hub_length) / 2.0)):
                bd.Box(b_key, t2 * 2.0, total_len, mode=bd.Mode.SUBTRACT)

    return builder.part

build.checks_func = check_spur_gear
