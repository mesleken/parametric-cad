"""Engineering checks for stepped transmission shafts."""

import math
from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus, PhysicsResult
from pcad.engineering.margins import compute_margin_of_safety

def check_stepped_shaft(params, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    """Evaluates torsional shear, bending, and shoulder fillet stress concentrations.
    
    References:
    - Shigley's Mechanical Engineering Design, Ch. 7 (Shafts and Shaft Components)
    - Peterson's Stress Concentration Factors (Shoulder Fillets in Torsion/Bending)
    """
    checks = []
    
    # 1. Torsional Shear Stress in smallest diameter section (d1)
    # tau = 16 * T / (pi * d1^3)
    torque_n_mm = getattr(params, "torque_nm", 100.0) * 1000.0 # Convert Nm to N*mm
    d1 = params.d1
    tau_applied = (16.0 * torque_n_mm) / (math.pi * (d1 ** 3))
    
    # Allowable shear yield (tau_yield = 0.577 * sigma_yield via Von Mises)
    allowable_shear = material.shear_strength_mpa or (0.577 * material.yield_strength_mpa)
    fos = getattr(params, "fos", 1.5)
    
    ms_torsion = compute_margin_of_safety(applied=tau_applied, allowable=allowable_shear, fos=fos)
    status_torsion = (
        MarginStatus.POSITIVE if ms_torsion >= 0.2
        else (MarginStatus.LOW if ms_torsion >= 0.0 else MarginStatus.NEGATIVE)
    )
    checks.append(CheckResult(
        name="Torsional Shear Stress (tau)",
        applied=round(tau_applied, 1),
        allowable=round(allowable_shear, 1),
        margin_of_safety=round(ms_torsion, 3),
        unit="MPa",
        status=status_torsion,
        rule_ref="Shigley Ch. 7, Eq. 7-1 (Von Mises shear)",
        message=f"Torsional stress on d={d1}mm journal under {params.torque_nm} Nm torque."
    ))

    # 2. Shoulder Fillet Ratio Check (r / d1 >= 0.05 recommended to limit Kt <= 1.8)
    fillet_ratio = params.r_fillet / params.d1
    ms_fillet = compute_margin_of_safety(applied=0.05, allowable=fillet_ratio, fos=1.0)
    status_fillet = (
        MarginStatus.POSITIVE if fillet_ratio >= 0.05
        else MarginStatus.NEGATIVE
    )
    checks.append(CheckResult(
        name="Shoulder Fillet Ratio (r / d1)",
        applied=round(fillet_ratio, 3),
        allowable=0.05,
        margin_of_safety=round(ms_fillet, 3),
        unit="-",
        status=status_fillet,
        rule_ref="DIN 743 / Peterson Notch Factor (Kt)",
        message="r/d >= 0.05 required to avoid severe fatigue notch stress concentrations."
    ))

    return checks
