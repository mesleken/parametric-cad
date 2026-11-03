"""Aerospace Bolted Splice Plate (Cıvatalı Ekleme / Bağlantı Plakası) Template."""

from typing import Annotated, List
from pydantic import BaseModel, Field, model_validator
from pcad.domain.materials import Material, MaterialDB
from pcad.domain.template import CheckResult, MarginStatus, PhysicsResult, UI, template
from pcad.engineering.margins import make_check_result

class SplicePlateParams(BaseModel):
    # Geometry
    plate_length: Annotated[float, Field(gt=40.0, le=800.0), UI(label={"en": "Plate Length (L)", "tr": "Plaka Boyu (L)"}, unit="mm", group="geometry", step=10.0)] = 160.0
    plate_width: Annotated[float, Field(gt=20.0, le=400.0), UI(label={"en": "Plate Width (W)", "tr": "Plaka Eni (W)"}, unit="mm", group="geometry", step=5.0)] = 60.0
    plate_thickness: Annotated[float, Field(gt=1.5, le=40.0), UI(label={"en": "Plate Thickness (t)", "tr": "Plaka Kalınlığı (t)"}, unit="mm", group="geometry", step=0.5)] = 5.0
    
    # Fastener Pattern
    bolt_dia: Annotated[float, Field(gt=3.0, le=30.0), UI(label={"en": "Bolt Diameter (d)", "tr": "Cıvata Çapı (d)"}, unit="mm", group="geometry", step=1.0)] = 8.0
    rows: Annotated[int, Field(ge=1, le=4), UI(label={"en": "Number of Rows", "tr": "Cıvata Sıra Sayısı"}, unit="-", group="geometry", step=1.0)] = 2
    cols_per_side: Annotated[int, Field(ge=1, le=6), UI(label={"en": "Cols per Side", "tr": "Taraf Başına Sütun"}, unit="-", group="geometry", step=1.0)] = 2
    pitch_x: Annotated[float, Field(gt=10.0, le=150.0), UI(label={"en": "Bolt Pitch (p)", "tr": "Cıvata Hatvesi (p)"}, unit="mm", group="geometry", step=2.0)] = 30.0
    gauge_y: Annotated[float, Field(gt=10.0, le=150.0), UI(label={"en": "Bolt Gauge (g)", "tr": "Cıvata Sıra Aralığı (g)"}, unit="mm", group="geometry", step=2.0)] = 30.0
    edge_x: Annotated[float, Field(gt=5.0, le=100.0), UI(label={"en": "Edge Distance (e)", "tr": "Uç Kenar Mesafesi (e)"}, unit="mm", group="geometry", step=1.0)] = 20.0
    
    # Loads
    axial_load_n: Annotated[float, Field(ge=0.0, le=1e7), UI(label={"en": "Axial Tension Load (F)", "tr": "Eksenel Çekme Yükü (F)"}, unit="N", group="loads", step=1000.0)] = 20000.0
    fos: Annotated[float, Field(gt=1.0, le=5.0), UI(label={"en": "Factor of Safety", "tr": "Emniyet Katsayısı"}, unit="-", group="advanced", step=0.1)] = 1.5

    @model_validator(mode="after")
    def validate_splice_plate(self):
        # Verify bolts fit inside plate width and length
        total_gauge = (self.rows - 1) * self.gauge_y if self.rows > 1 else 0
        if total_gauge + (2.0 * self.bolt_dia) >= self.plate_width:
            raise ValueError("Bolt pattern exceeds plate width boundary.")
            
        span_per_side = (self.cols_per_side - 1) * self.pitch_x if self.cols_per_side > 1 else 0
        if (2.0 * self.edge_x) + (2.0 * span_per_side) >= self.plate_length:
            raise ValueError("Bolt pattern exceeds plate length boundary.")
        return self

@template(
    id="aero.splice_plate",
    version="1.0.0",
    category="Aerospace & Structural",
    name={"en": "Bolted Splice Plate", "tr": "Cıvatalı Ekleme Plakası"},
    description={
        "en": "Structural double-shear or butt splice plate with multi-row fastener pattern and net-section verification.",
        "tr": "Çok sıralı cıvata dizilimine ve net kesit çekme/yataklama analizine sahip yapısal ekleme plakası."
    },
    params=SplicePlateParams,
    default_material="Al7075-T6"
)
def build(p: SplicePlateParams):
    from build123d import (
        BuildPart, Box, Cylinder, Locations, Mode, Align
    )
    
    with BuildPart() as builder:
        # 1. Main rectangular plate
        Box(p.plate_length, p.plate_width, p.plate_thickness, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        
        # 2. Fastener holes symmetrically placed on both halves
        hole_locs = []
        y_start = -((p.rows - 1) * p.gauge_y) / 2.0 if p.rows > 1 else 0.0
        
        for side in (-1, 1): # Left half and right half
            x_base = side * (p.plate_length / 2.0 - p.edge_x)
            for c in range(p.cols_per_side):
                x_pos = x_base - (side * c * p.pitch_x)
                for r in range(p.rows):
                    y_pos = y_start + (r * p.gauge_y)
                    hole_locs.append((x_pos, y_pos, 0))
                    
        with Locations(hole_locs):
            Cylinder(radius=p.bolt_dia / 2.0, height=p.plate_thickness * 2.0, mode=Mode.SUBTRACT)
            
    return builder.part

def checks(p: SplicePlateParams, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    results: List[CheckResult] = []
    
    # 1. Net-Section Tension across critical fastener row
    # Net Width = plate_width - (rows * bolt_dia)
    net_width = max(p.plate_width - (p.rows * p.bolt_dia), 1e-4)
    net_area = net_width * p.plate_thickness
    sigma_net = p.axial_load_n / net_area
    results.append(make_check_result(
        name="Net-Section Tension",
        applied=sigma_net,
        allowable=material.ultimate_strength_mpa,
        fos=p.fos,
        unit="MPa",
        rule_ref="Bruhn D2 / Niu Airframe Design",
        message="Tensile rupture across critical bolt row cross-section"
    ))
    
    # 2. Fastener Bearing Stress (total fasteners = 2 * cols_per_side * rows per joint)
    total_bolts_per_side = max(p.cols_per_side * p.rows, 1)
    load_per_bolt = p.axial_load_n / total_bolts_per_side
    bearing_area_per_bolt = max(p.bolt_dia * p.plate_thickness, 1e-4)
    sigma_brg = load_per_bolt / bearing_area_per_bolt
    allowable_brg = material.bearing_ult_mpa or (1.5 * material.ultimate_strength_mpa)
    results.append(make_check_result(
        name="Bolt Hole Bearing Stress",
        applied=sigma_brg,
        allowable=allowable_brg,
        fos=p.fos,
        unit="MPa",
        rule_ref="Bruhn D2.4",
        message="Average bearing stress across fastener contact surfaces"
    ))
    
    # 3. Fastener Shear Stress with Row Load Concentration (Bruhn D2 / Niu Ch 7)
    # Differential strain in multi-row lap joints causes outer fastener row to carry ~15% higher load
    row_concentration_factor = 1.15 if p.cols_per_side > 1 else 1.0
    critical_bolt_load_n = load_per_bolt * row_concentration_factor
    a_bolt_shear = (3.14159265 / 4.0) * (p.bolt_dia ** 2)
    tau_bolt = critical_bolt_load_n / max(a_bolt_shear, 1e-4)
    # High-strength shear allowable (NAS bolt or matched 0.60 * Ftu)
    tau_allowable = 0.60 * material.ultimate_strength_mpa
    results.append(make_check_result(
        name="Fastener Shear Stress",
        applied=tau_bolt,
        allowable=tau_allowable,
        fos=p.fos,
        unit="MPa",
        rule_ref="Bruhn D2.1 / Niu Ch. 7",
        message=f"Outer row fastener single shear (eta={row_concentration_factor:.2f}, load={critical_bolt_load_n:.0f} N)."
    ))

    # 4. Aerospace Fastener Spacing Rules
    # Edge distance ratio e / d >= 2.0
    ed_ratio = p.edge_x / p.bolt_dia
    results.append(CheckResult(
        name="Edge Distance (e / d)",
        status=MarginStatus.POSITIVE if ed_ratio >= 2.0 else (MarginStatus.LOW if ed_ratio >= 1.5 else MarginStatus.NEGATIVE),
        margin_of_safety=round((ed_ratio / 2.0) - 1.0, 2),
        applied=round(ed_ratio, 2),
        allowable=2.0,
        unit="ratio",
        rule_ref="MIL-HDBK-5J / MS33540",
        message="Standard guideline: e/d >= 2.0 prevents edge breakout"
    ))
    
    # Fastener pitch ratio p / d >= 3.0
    pd_ratio = p.pitch_x / p.bolt_dia
    results.append(CheckResult(
        name="Bolt Pitch (p / d)",
        status=MarginStatus.POSITIVE if pd_ratio >= 3.0 else (MarginStatus.LOW if pd_ratio >= 2.5 else MarginStatus.NEGATIVE),
        margin_of_safety=round((pd_ratio / 3.0) - 1.0, 2),
        applied=round(pd_ratio, 2),
        allowable=3.0,
        unit="ratio",
        rule_ref="MIL-HDBK-5J / MS33540",
        message="Standard guideline: p/d >= 3.0 avoids high stress interaction"
    ))
    
    return results

build.checks_func = checks
