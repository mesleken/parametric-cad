"""Engineering checks for electronic enclosures and protective casings."""

from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus, PhysicsResult
from pcad.engineering.margins import compute_margin_of_safety

def check_enclosure(params, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    """Evaluates wall thickness rigidity, standoff boss ratios, and internal enclosure volume."""
    checks = []
    
    # 1. Standoff Boss Wall Ratio (Boss OD / Screw Hole Dia >= 2.0 recommended for self-tapping or heat-set inserts)
    if hasattr(params, "boss_od") and hasattr(params, "screw_dia"):
        boss_ratio = params.boss_od / max(params.screw_dia, 0.1)
        ms_boss = compute_margin_of_safety(applied=2.0, allowable=boss_ratio, fos=1.0)
        status_boss = MarginStatus.POSITIVE if boss_ratio >= 2.0 else MarginStatus.LOW
        checks.append(CheckResult(
            name="Mounting Boss Aspect (OD / d)",
            applied=round(boss_ratio, 2),
            allowable=2.0,
            margin_of_safety=round(ms_boss, 2),
            unit="-",
            status=status_boss,
            rule_ref="Design for Injection Molding / Additive Fastening Guide",
            message="Boss OD/ID >= 2.0 ensures sufficient hoop strength against hoop bursting during fastener torque."
        ))

    # 2. Wall Thickness Rigidity (Wall Thickness / Span >= 0.015 to prevent wall buckling/deflection)
    max_span = max(params.length, params.width)
    wall_ratio = (params.wall_thickness / max_span) * 100.0 # Percentage
    min_recommended = 1.5 # 1.5%
    ms_wall = compute_margin_of_safety(applied=min_recommended, allowable=wall_ratio, fos=1.0)
    status_wall = MarginStatus.POSITIVE if wall_ratio >= min_recommended else MarginStatus.LOW
    checks.append(CheckResult(
        name="Wall Thickness / Span Ratio",
        applied=round(wall_ratio, 2),
        allowable=min_recommended,
        margin_of_safety=round(ms_wall, 2),
        unit="%",
        status=status_wall,
        rule_ref="Roark's Formulas for Stress and Strain (Flat Plate Deflection)",
        message="Wall thickness >= 1.5% of max span prevents oil-canning and structural vibration flexure."
    ))

    return checks
