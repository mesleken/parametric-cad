"""Engineering checks for stepped transmission shafts."""

import math
from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus, PhysicsResult
from pcad.engineering.margins import compute_margin_of_safety, evaluate_status

def check_stepped_shaft(params, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    """Evaluates torsional shear, shoulder fillet notch effect, and torsional rigidity.
    
    References:
    - DIN 743 (Load capacity calculation for shafts and axles)
    - Peterson's Stress Concentration Factors (Shoulder Fillets & Keyways in Torsion)
    - Shigley's Mechanical Engineering Design, Ch. 7 (Shafts and Shaft Components)
    """
    checks = []
    
    torque_n_mm = getattr(params, "torque_nm", 150.0) * 1000.0  # Convert Nm to N*mm
    d_min = min(params.d1, params.d3)
    tau_nominal = (16.0 * torque_n_mm) / (math.pi * (d_min ** 3))
    
    # Allowable shear yield via Von Mises distortion energy: tau_y = 0.577 * sigma_yield
    allowable_shear = 0.577 * material.yield_strength_mpa
    fos = getattr(params, "fos", 1.5)
    
    # 1. Torsional Shear Stress (nominal on d_min section)
    ms_torsion = compute_margin_of_safety(applied=tau_nominal, allowable=allowable_shear, fos=fos)
    status_torsion = evaluate_status(ms_torsion)
    checks.append(CheckResult(
        name="Torsional Shear Stress (tau)",
        applied=round(tau_nominal, 1),
        allowable=round(allowable_shear, 1),
        margin_of_safety=round(ms_torsion, 3),
        unit="MPa",
        status=status_torsion,
        rule_ref="Shigley Ch. 7, Eq. 7-1 (Von Mises shear)",
        message=f"Torsional stress on smallest journal section (d={d_min}mm) under {params.torque_nm} N·m torque."
    ))

    # 2. Peterson / DIN 743 Shoulder Fillet Notch Factor (Kts)
    r = max(params.r_fillet, 0.1)
    d_step = max(params.d2, d_min * 1.05)
    r_over_d = r / d_min
    d_over_d = d_step / d_min
    
    # Peterson standard empirical formula for stepped shaft in torsion (Shigley A-15-8):
    kts_fillet = 1.0 + (0.6 / math.sqrt(r_over_d)) * ((d_over_d - 1.0) / d_over_d)
    
    # DIN 6885 Form A Keyway Notch Factor
    has_keyway = getattr(params, "has_keyway", getattr(params, "keyway_enabled", True))
    kts_keyway = 1.6 if has_keyway else 1.0
    kts_eff = max(kts_fillet, kts_keyway)
    tau_peak = tau_nominal * kts_eff
    
    ms_peak = compute_margin_of_safety(applied=tau_peak, allowable=allowable_shear, fos=fos)
    status_peak = evaluate_status(ms_peak)
    checks.append(CheckResult(
        name="Peak Fillet/Keyway Shear (tau_max)",
        applied=round(tau_peak, 1),
        allowable=round(allowable_shear, 1),
        margin_of_safety=round(ms_peak, 3),
        unit="MPa",
        status=status_peak,
        rule_ref="DIN 743 / Peterson Kts",
        message=f"Peak shear at fillet/keyway (nominal={tau_nominal:.1f} MPa, Kts={kts_eff:.2f}) under {params.torque_nm} N·m."
    ))

    # 3. Shoulder Fillet Ratio Check (r / d_min >= 0.05 recommended to limit Kt <= 1.8)
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
        rule_ref="DIN 743 Notch Proportions",
        message="r/d >= 0.05 required to avoid severe fatigue notch stress concentrations."
    ))

    # 4. Torsional Rigidity / Twist Angle Check (DIN 743 / Shigley limit: theta <= 1.0 deg)
    # Shear modulus G = E / [2 * (1 + nu)]
    e_mpa = material.elastic_modulus_gpa * 1000.0
    nu = material.poisson_ratio
    g_mpa = e_mpa / (2.0 * (1.0 + nu))
    
    # Sum twist angle over the three segments: theta = sum(T * L_i / (G * J_i))
    sections = [
        (params.d1, params.l1),
        (params.d2, params.l2),
        (params.d3, params.l3),
    ]
    total_twist_rad = 0.0
    total_len_mm = sum(l for _, l in sections)
    for dia, length in sections:
        j_polar = (math.pi * (dia ** 4)) / 32.0
        total_twist_rad += (torque_n_mm * length) / (g_mpa * j_polar)
        
    total_twist_deg = total_twist_rad * (180.0 / math.pi)
    twist_per_meter = total_twist_deg / max(total_len_mm / 1000.0, 1e-4)
    allowable_total_twist_deg = 1.0  # 1.0 deg limit across transmission shaft length
    
    ms_twist = compute_margin_of_safety(applied=total_twist_deg, allowable=allowable_total_twist_deg, fos=1.0)
    status_twist = evaluate_status(ms_twist)
    checks.append(CheckResult(
        name="Torsional Rigidity / Twist (theta)",
        applied=round(total_twist_deg, 2),
        allowable=allowable_total_twist_deg,
        margin_of_safety=round(ms_twist, 3),
        unit="deg",
        status=status_twist,
        rule_ref="DIN 743 / Shigley Shaft Rigidity",
        message=f"Total twist = {total_twist_deg:.2f}° across {total_len_mm:.0f} mm span ({twist_per_meter:.2f}°/m, G={g_mpa:.0f} MPa)."
    ))

    return checks
