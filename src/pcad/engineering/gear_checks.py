"""Engineering checks for involute spur gears."""

import math
from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus, PhysicsResult
from pcad.engineering.margins import compute_margin_of_safety

def check_spur_gear(params, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    """Evaluates Lewis tooth bending stress and kinematic undercut limit.
    
    References:
    - AGMA 2001-D04 / ISO 6336 (Calculation of load capacity of spur and helical gears)
    - Lewis Equation for Gear Tooth Bending Strength
    """
    checks = []
    m = params.module # Module (mm)
    z = params.num_teeth
    b = params.face_width
    pitch_dia = m * z
    
    # Tangential load: Ft = 2 * T / d_pitch
    torque_n_mm = getattr(params, "torque_nm", 50.0) * 1000.0
    f_t = (2.0 * torque_n_mm) / pitch_dia
    
    # Lewis form factor approximation for 20 deg full-depth involute teeth:
    # Y ~= 0.154 - 0.912 / z
    y_lewis = max(0.154 - (0.912 / max(z, 5)), 0.05)
    
    # Lewis tooth root bending stress: sigma = Ft / (b * m * Y)
    sigma_bending = f_t / (b * m * y_lewis)
    
    allowable_bending = material.yield_strength_mpa * 0.70 # Tooth root fatigue allowable
    fos = getattr(params, "fos", 1.5)
    
    ms_bending = compute_margin_of_safety(applied=sigma_bending, allowable=allowable_bending, fos=fos)
    status_bending = (
        MarginStatus.POSITIVE if ms_bending >= 0.2
        else (MarginStatus.LOW if ms_bending >= 0.0 else MarginStatus.NEGATIVE)
    )
    checks.append(CheckResult(
        name="Lewis Tooth Bending Stress",
        applied=round(sigma_bending, 1),
        allowable=round(allowable_bending, 1),
        margin_of_safety=round(ms_bending, 3),
        unit="MPa",
        status=status_bending,
        rule_ref="AGMA 2001 / Lewis Bending Equation",
        message=f"Root tensile bending stress under Ft={f_t:.0f} N tangential tooth load."
    ))

    # 2. Minimum Teeth Count for Undercut (z >= 17 for standard 20 deg pressure angle)
    ms_undercut = compute_margin_of_safety(applied=17.0, allowable=float(z), fos=1.0)
    status_undercut = MarginStatus.POSITIVE if z >= 17 else MarginStatus.LOW
    checks.append(CheckResult(
        name="Tooth Undercut Limit (z >= 17)",
        applied=float(z),
        allowable=17.0,
        margin_of_safety=round(ms_undercut, 2),
        unit="teeth",
        status=status_undercut,
        rule_ref="ISO 6336-1 (Interference & Undercutting)",
        message="Gears with z < 17 require positive profile shift (+x) to eliminate pin undercut."
    ))

    return checks
