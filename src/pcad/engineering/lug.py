"""Aerospace Attachment Lug engineering analysis (Bruhn / Airframe Stress Analysis)."""

from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus
from pcad.engineering.margins import make_check_result

def check_lug(
    W: float,
    D: float,
    e: float,
    t: float,
    F_axial_N: float,
    material: Material,
    K_tu: float = 1.0,
    fos: float = 1.5
) -> List[CheckResult]:
    """Evaluates an axially loaded straight lug.
    
    References:
    - Bruhn, E.F., 'Analysis and Design of Flight Vehicle Structures', Chapter D1.
    - NASA-CR-505 'Lug Sizing and Stress Analysis'.
    """
    results: List[CheckResult] = []
    
    # 1. Net-Section Tension
    # Area = (W - D) * t
    net_area = max((W - D) * t, 1e-4)
    sigma_net = F_axial_N / net_area
    allowable_net = material.ultimate_strength_mpa * K_tu
    results.append(make_check_result(
        name="Net-Section Tension",
        applied=sigma_net,
        allowable=allowable_net,
        fos=fos,
        unit="MPa",
        rule_ref="Bruhn D1.2",
        message="Tensile rupture across pin hole net area"
    ))
    
    # 2. Pin Bearing Stress
    # Area = D * t
    brg_area = max(D * t, 1e-4)
    sigma_brg = F_axial_N / brg_area
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
    tau_out = F_axial_N / shear_area
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
    
    # 4. Geometric Proportions (Aerospace Design Rules)
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
