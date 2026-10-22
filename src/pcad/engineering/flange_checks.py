"""Flange geometric rule checks (Bolt ligament, edge margin, clearance)."""

import math
from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus

def check_flange(
    outer_dia: float,
    inner_dia: float,
    pcd: float,
    num_bolts: int,
    bolt_hole_dia: float,
    flange_thickness: float,
    design_pressure_mpa: float = 1.0,
    material: Material = None,
    fos: float = 1.5
) -> List[CheckResult]:
    """Pure geometric and basic ligament checks for flanges.
    
    NOTE: As stated in design guidelines, this is for preliminary design / layout check.
    It does not replace full ASME Section VIII or EN 13445 pressure vessel calculation.
    """
    results: List[CheckResult] = []
    
    # 1. Bolt-to-bolt chord distance (Ligament)
    # Pitch distance along bolt circle PCD
    angle_rad = (2.0 * math.pi) / max(num_bolts, 1)
    chord_pitch = pcd * math.sin(angle_rad / 2.0)
    ligament = chord_pitch - bolt_hole_dia
    # Rule of thumb: ligament should be at least 1.0 * bolt_hole_dia for wrench clearance and web strength
    min_required_ligament = 1.0 * bolt_hole_dia
    ms_ligament = (ligament / max(min_required_ligament, 1e-4)) - 1.0
    results.append(CheckResult(
        name="Bolt-to-Bolt Ligament",
        status=MarginStatus.POSITIVE if ms_ligament >= 0.0 else MarginStatus.NEGATIVE,
        margin_of_safety=round(ms_ligament, 2),
        applied=round(ligament, 2),
        allowable=round(min_required_ligament, 2),
        unit="mm",
        rule_ref="DIN 2501 / ASME B16.5 Clearance Rule",
        message="Web thickness between adjacent bolt holes for wrench clearance"
    ))
    
    # 2. Outer Edge Distance: (OD - PCD) / 2
    outer_edge_dist = (outer_dia - pcd) / 2.0
    min_outer_edge = 1.25 * bolt_hole_dia
    ms_edge = (outer_edge_dist / max(min_outer_edge, 1e-4)) - 1.0
    results.append(CheckResult(
        name="Outer Edge Distance",
        status=MarginStatus.POSITIVE if ms_edge >= 0.0 else MarginStatus.NEGATIVE,
        margin_of_safety=round(ms_edge, 2),
        applied=round(outer_edge_dist, 2),
        allowable=round(min_outer_edge, 2),
        unit="mm",
        rule_ref="Standard Bolted Joint Margin (1.25*D)",
        message="Flange outer rim width to prevent edge breakout"
    ))
    
    return results
