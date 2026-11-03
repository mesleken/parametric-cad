"""Engineering checks for stepped transmission shafts."""

import math
from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus, PhysicsResult
from pcad.engineering.margins import compute_margin_of_safety, evaluate_status

def check_stepped_shaft(params, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    """Evaluates torsional shear and shoulder fillet stress concentrations.
    
    References:
    - Shigley's Mechanical Engineering Design, Ch. 7 (Shafts and Shaft Components)
    - Peterson's Stress Concentration Factors (Shoulder Fillets in Torsion/Bending)
    """
    checks = []
    
    # 1. Torsional Shear Stress in smallest diameter section d_min = min(d1, d3)
    # tau = 16 * T / (pi * d_min^3)
    torque_n_mm = getattr(params, "torque_nm", 150.0) * 1000.0 # Convert Nm to N*mm
    d_min = min(params.d1, params.d3)
    tau_applied = (16.0 * torque_n_mm) / (math.pi * (d_min ** 3))
    
    # Allowable shear yield via Von Mises distortion energy: tau_y = 0.577 * sigma_yield
    allowable_shear = 0.577 * material.yield_strength_mpa
    fos = getattr(params, "fos", 1.5)
    
    ms_torsion = compute_margin_of_safety(applied=tau_applied, allowable=allowable_shear, fos=fos)
    status_torsion = evaluate_status(ms_torsion)
    checks.append(CheckResult(
        name="Torsional Shear Stress (tau)",
        applied=round(tau_applied, 1),
        allowable=round(allowable_shear, 1),
        margin_of_safety=round(ms_torsion, 3),
        unit="MPa",
        status=status_torsion,
        rule_ref="Shigley Ch. 7, Eq. 7-1 (Von Mises shear)",
        message=f"Torsional stress on smallest journal section (d={d_min}mm) under {params.torque_nm} N·m torque."
    ))

    # 2. Shoulder Fillet Ratio Check (r / d_min >= 0.05 recommended to limit Kt <= 1.8)
    fillet_ratio = params.r_fillet / d_min
    ms_fillet = compute_margin_of_safety(applied=0.05, allowable=fillet_ratio, fos=1.0)
    status_fillet = evaluate_status(ms_fillet)
    checks.append(CheckResult(
        name="Shoulder Fillet Ratio (r / d_min)",
        applied=round(fillet_ratio, 3),
        allowable=0.05,
        margin_of_safety=round(ms_fillet, 3),
        unit="-",
        status=status_fillet,
        rule_ref="DIN 743 / Peterson Notch Factor (Kt)",
        message="r/d >= 0.05 required to avoid severe fatigue notch stress concentrations."
    ))

    return checks
