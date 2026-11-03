"""Engineering checks for involute spur gears according to ISO 6336 and AGMA 2001."""

import math
from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus, PhysicsResult
from pcad.engineering.margins import compute_margin_of_safety, evaluate_status

def check_spur_gear(params, material: Material, physics: PhysicsResult) -> List[CheckResult]:
    """Evaluates tooth root bending (ISO 6336/Lewis + Dolan-Broghamer), 
    Hertzian contact (pitting) stress, and profile shift undercut limit.
    
    References:
    - ISO 6336-1 to ISO 6336-5 (Calculation of load capacity of spur and helical gears)
    - AGMA 2001-D04 (Fundamental Rating Factors and Calculation Methods for Involute Spur Gear Teeth)
    - Dolan & Broghamer (Stress Concentration Factors for Gear Teeth)
    """
    checks = []
    m = params.module  # Module (mm)
    z = params.num_teeth
    b = params.face_width
    pitch_dia = m * z
    x = getattr(params, "profile_shift", 0.0)
    gear_ratio = max(getattr(params, "gear_ratio", 1.0), 1.0)
    fos = getattr(params, "fos", 1.5)
    
    # Tangential load: Ft = 2 * T / d_pitch
    torque_n_mm = getattr(params, "torque_nm", 50.0) * 1000.0
    f_t = (2.0 * torque_n_mm) / pitch_dia
    
    # 1. Tooth Root Bending Stress with Dolan-Broghamer Stress Concentration Kf
    # Lewis form factor approximation for 20 deg full-depth involute: Y ~= 0.154 - 0.912 / z
    y_base = max(0.154 - (0.912 / max(z, 5)), 0.05)
    # Profile shift modification to tooth thickness at root:
    y_lewis = y_base * (1.0 + 0.30 * x)
    
    # Dolan-Broghamer stress concentration factor Kf:
    # Kf = H + (t / rf)^L * (t / hf)^M for 20 deg full depth
    # Typical values: H = 0.18, L = 0.15, M = 0.45, t/rf ~ 4.13, t/hf ~ 1.25 -> Kf ~ 1.55
    r_f = 0.38 * m
    h_f = 1.25 * m
    t_root = 1.57 * m * (1.0 + 0.2 * x)
    kf = 0.18 + ((t_root / max(r_f, 1e-3)) ** 0.15) * ((t_root / max(h_f, 1e-3)) ** 0.45)
    
    # Root bending stress: sigma_F = (Ft * Kf) / (b * m * Y)
    sigma_bending = (f_t * kf) / (b * m * y_lewis)
    
    # Allowable root bending: endurance limit or 0.70 * yield strength
    allowable_bending = (
        material.endurance_limit_mpa 
        if material.endurance_limit_mpa > 0 
        else 0.70 * material.yield_strength_mpa
    )
    
    ms_bending = compute_margin_of_safety(applied=sigma_bending, allowable=allowable_bending, fos=fos)
    status_bending = evaluate_status(ms_bending)
    checks.append(CheckResult(
        name="Tooth Root Bending (ISO 6336 / AGMA)",
        applied=round(sigma_bending, 1),
        allowable=round(allowable_bending, 1),
        margin_of_safety=round(ms_bending, 3),
        unit="MPa",
        status=status_bending,
        rule_ref="ISO 6336 / Dolan-Broghamer Kf",
        message=f"Root tensile stress (Ft={f_t:.0f} N, Kf={kf:.2f}, Y={y_lewis:.3f}, x={x:+.2f})."
    ))

    # 2. Hertz Surface Contact / Pitting Stress (ISO 6336-2 / AGMA 2001)
    # sigma_H = ZE * ZH * sqrt( (Ft / (b * dp)) * ((u + 1) / u) )
    # Zone factor for 20 deg alpha: ZH = sqrt(2 / sin(40 deg)) ~= 1.764
    z_h = math.sqrt(2.0 / math.sin(math.radians(40.0)))
    
    # Elasticity factor ZE = sqrt( E / (2 * pi * (1 - nu^2)) )
    e_mpa = material.elastic_modulus_gpa * 1000.0
    nu = material.poisson_ratio
    z_e = math.sqrt(e_mpa / (2.0 * math.pi * max(1.0 - (nu ** 2), 0.1)))
    
    u = gear_ratio
    sigma_contact = z_e * z_h * math.sqrt((f_t / (b * pitch_dia)) * ((u + 1.0) / u))
    
    # Allowable contact fatigue limit (pitting limit sigma_H,lim)
    # ISO 6336-5: for through-hardened metallic alloys, sigma_Hlim ~= 2.5 * HB + 150 MPa
    if material.hardness_hb > 0:
        allowable_contact = 2.5 * material.hardness_hb + 150.0
    else:
        allowable_contact = 0.85 * material.yield_strength_mpa
        
    ms_contact = compute_margin_of_safety(applied=sigma_contact, allowable=allowable_contact, fos=fos)
    status_contact = evaluate_status(ms_contact)
    checks.append(CheckResult(
        name="Hertz Contact / Pitting Stress (sigma_H)",
        applied=round(sigma_contact, 1),
        allowable=round(allowable_contact, 1),
        margin_of_safety=round(ms_contact, 3),
        unit="MPa",
        status=status_contact,
        rule_ref="ISO 6336-2 / AGMA 2001 (Pitting)",
        message=f"Hertzian flank contact pressure (ZE={z_e:.0f} MPa^0.5, u={u:.1f}, HB={material.hardness_hb})."
    ))

    # 3. Minimum Teeth Count for Undercut (z >= 17 * (1 - x))
    z_min_required = max(17.0 * (1.0 - x), 5.0)
    ms_undercut = compute_margin_of_safety(applied=z_min_required, allowable=float(z), fos=1.0)
    status_undercut = MarginStatus.POSITIVE if z >= z_min_required else MarginStatus.LOW
    checks.append(CheckResult(
        name="Tooth Undercut Limit",
        applied=float(z),
        allowable=round(z_min_required, 1),
        margin_of_safety=round(ms_undercut, 2),
        unit="teeth",
        status=status_undercut,
        rule_ref="ISO 53 / ISO 6336 (Pin Undercut)",
        message=f"z >= {z_min_required:.1f} required without pin undercut (profile shift x={x:+.2f})."
    ))

    return checks
