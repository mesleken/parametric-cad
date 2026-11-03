"""Aerospace Attachment Lug engineering analysis (Bruhn / Airframe Stress Analysis)."""

import math
from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus
from pcad.engineering.margins import compute_margin_of_safety, evaluate_status, make_check_result

def check_lug(
    W: float,
    D: float,
    e: float,
    t: float,
    F_axial_N: float,
    material: Material,
    K_tu: float = 1.0,
    load_angle_deg: float = 0.0,
    fos: float = 1.5
) -> List[CheckResult]:
    """Evaluates an axially or obliquely loaded straight lug per Bruhn Chapter D1 / NASA-CR-505.
    
    References:
    - Bruhn, E.F., 'Analysis and Design of Flight Vehicle Structures', Chapter D1.
    - NASA-CR-505 'Lug Sizing and Stress Analysis'.
    """
    results: List[CheckResult] = []
    
    # Resolve axial and transverse load components if obliquely loaded
    theta_rad = math.radians(load_angle_deg)
    f_axial = F_axial_N * math.cos(theta_rad)
    f_trans = F_axial_N * math.sin(theta_rad)
    
    # 1. Net-Section Tension
    # Area = (W - D) * t
    net_area = max((W - D) * t, 1e-4)
    sigma_net = f_axial / net_area
    
    # Bruhn D1.2: calculate empirical net section factor if default 1.0
    # Ktu drops for low W/D and high yield-to-tensile ratio alloys (e.g. 7075-T6)
    eff_k_tu = K_tu
    if abs(K_tu - 1.0) < 1e-3 and W > D:
        ratio_ty_tu = min(material.yield_strength_mpa / max(material.ultimate_strength_mpa, 1.0), 1.0)
        eff_k_tu = max(0.65, min(1.0, 1.05 - 0.22 * (D / W) * ratio_ty_tu))

    allowable_net = material.ultimate_strength_mpa * eff_k_tu
    results.append(make_check_result(
        name="Net-Section Tension",
        applied=sigma_net,
        allowable=allowable_net,
        fos=fos,
        unit="MPa",
        rule_ref="Bruhn D1.2 / NASA-CR-505",
        message=f"Tensile rupture across pin hole net area (Ktu={eff_k_tu:.2f})"
    ))
    
    # 2. Pin Bearing Stress
    # Area = D * t
    brg_area = max(D * t, 1e-4)
    sigma_brg = f_axial / brg_area
    allowable_brg = material.bearing_ult_mpa or (1.5 * material.ultimate_strength_mpa)
    results.append(make_check_result(
        name="Pin Bearing Stress",
        applied=sigma_brg,
        allowable=allowable_brg,
        fos=fos,
        unit="MPa",
        rule_ref="Bruhn D1.3",
        message="Hole local crushing / bearing yield"
    ))
    
    # 3. Shear Tear-Out (40-deg / transverse shear)
    # Area = 2 * (e - D/2) * t
    shear_area = max(2.0 * (e - (D / 2.0)) * t, 1e-4)
    tau_out = f_axial / shear_area
    allowable_shear = material.shear_strength_mpa
    results.append(make_check_result(
        name="Shear Tear-Out",
        applied=tau_out,
        allowable=allowable_shear,
        fos=fos,
        unit="MPa",
        rule_ref="Bruhn D1.4",
        message="Double transverse shear failure along hole edge"
    ))
    
    # 4. Oblique Load Interaction (Bruhn D1.5 / NASA-CR-505)
    if load_angle_deg > 0.5:
        # Transverse ultimate capacity: P_tr = K_tr * A_brg * Ftu
        # K_tr approximation from Bruhn D1.5 curves based on e/D and W/D
        k_tr = min(max(0.6, 0.45 * (e / max(D, 1e-3))), 1.2)
        p_tr_cap = k_tr * brg_area * material.ultimate_strength_mpa
        
        # Axial ultimate capacity
        p_ax_cap = min(net_area * allowable_net, brg_area * allowable_brg, shear_area * allowable_shear)
        
        r_ax = (f_axial * fos) / max(p_ax_cap, 1e-4)
        r_tr = (f_trans * fos) / max(p_tr_cap, 1e-4)
        inter = (r_ax ** 1.6) + (r_tr ** 1.6)
        ms_oblique = (1.0 / max(inter ** (1.0 / 1.6), 1e-4)) - 1.0
        status_oblique = evaluate_status(ms_oblique)
        results.append(CheckResult(
            name="Oblique Load Interaction (R_ax^1.6 + R_tr^1.6)",
            applied=round(inter, 3),
            allowable=1.0,
            margin_of_safety=round(ms_oblique, 3),
            unit="ratio",
            status=status_oblique,
            rule_ref="Bruhn D1.5 / NASA-CR-505",
            message=f"Biaxial load interaction at {load_angle_deg:.1f}° inclination angle"
        ))
    
    # 5. Geometric Proportions (Aerospace Design Rules)
    # e/D ratio >= 1.5
    e_d_ratio = e / D if D > 0 else 0
    results.append(CheckResult(
        name="e / D Ratio",
        status=MarginStatus.POSITIVE if e_d_ratio >= 1.5 else (MarginStatus.LOW if e_d_ratio >= 1.2 else MarginStatus.NEGATIVE),
        margin_of_safety=round((e_d_ratio / 1.5) - 1.0, 2),
        applied=round(e_d_ratio, 2),
        allowable=1.5,
        unit="ratio",
        rule_ref="MIL-HDBK-5J / Bruhn",
        message="Aerospace guideline: e/D >= 1.5 prevents premature tear-out"
    ))
    
    # W/D ratio >= 2.0
    w_d_ratio = W / D if D > 0 else 0
    results.append(CheckResult(
        name="W / D Ratio",
        status=MarginStatus.POSITIVE if w_d_ratio >= 2.0 else (MarginStatus.LOW if w_d_ratio >= 1.6 else MarginStatus.NEGATIVE),
        margin_of_safety=round((w_d_ratio / 2.0) - 1.0, 2),
        applied=round(w_d_ratio, 2),
        allowable=2.0,
        unit="ratio",
        rule_ref="MIL-HDBK-5J / Bruhn",
        message="Aerospace guideline: W/D >= 2.0 ensures uniform stress distribution"
    ))
    
    return results
