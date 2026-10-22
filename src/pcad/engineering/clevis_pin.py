"""U-Clevis fitting and pin shear/bending analysis."""

import math
from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult
from pcad.engineering.margins import make_check_result

def check_clevis(
    gap: float,
    t_prong: float,
    D_pin: float,
    W_prong: float,
    F_axial_N: float,
    material: Material,
    pin_material: Material,
    fos: float = 1.5
) -> List[CheckResult]:
    results: List[CheckResult] = []
    
    # 1. Double Shear on Pin
    # Pin Area = 2 * (pi / 4 * D^2)
    a_pin_single = (math.pi / 4.0) * (D_pin ** 2)
    tau_pin = F_axial_N / max(2.0 * a_pin_single, 1e-4)
    results.append(make_check_result(
        name="Pin Double Shear",
        applied=tau_pin,
        allowable=pin_material.shear_strength_mpa,
        fos=fos,
        unit="MPa",
        rule_ref="Shigley 8-1",
        message="Shear failure across two pin cross-sections"
    ))
    
    # 2. Prong Bearing (total area = 2 * t_prong * D_pin)
    a_brg_total = max(2.0 * t_prong * D_pin, 1e-4)
    sigma_brg = F_axial_N / a_brg_total
    allowable_brg = material.bearing_ult_mpa or (1.5 * material.ultimate_strength_mpa)
    results.append(make_check_result(
        name="Clevis Prong Bearing",
        applied=sigma_brg,
        allowable=allowable_brg,
        fos=fos,
        unit="MPa",
        rule_ref="Bruhn D1.3",
        message="Local crushing on two clevis prongs"
    ))
    
    # 3. Pin Bending (approximate beam bending between prong centers)
    # Moment M = (F/2) * (t_prong/4 + gap/2)
    arm = (t_prong / 4.0) + (gap / 2.0)
    m_bend = (F_axial_N / 2.0) * arm # N*mm
    # Section modulus Z = pi * D^3 / 32
    z_pin = (math.pi * (D_pin ** 3)) / 32.0
    sigma_bend = m_bend / max(z_pin, 1e-4)
    results.append(make_check_result(
        name="Pin Bending Stress",
        applied=sigma_bend,
        allowable=pin_material.yield_strength_mpa,
        fos=fos,
        unit="MPa",
        rule_ref="Peterson Stress Concentration / Shigley",
        message="Flexural bending stress at pin center"
    ))
    
    return results
