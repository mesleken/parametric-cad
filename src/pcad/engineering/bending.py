"""Gusseted bracket / L-bracket flexural stress, deflection, and formability checks."""

import math
from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus
from pcad.engineering.margins import compute_margin_of_safety, evaluate_status, make_check_result

def check_bracket(
    length_mm: float,
    width_mm: float,
    thickness_mm: float,
    inner_radius_mm: float,
    load_n: float,
    material: Material,
    gusset_count: int = 1,
    gusset_thickness_mm: float = 4.0,
    fos: float = 1.5,
    gusset_depth_mm: float = 0.0,
    **kwargs
) -> List[CheckResult]:
    """Evaluates cantilever bending stress via Steiner's parallel axis theorem,
    cantilever tip deflection stiffness (L/250), and bend radius formability.
    
    References:
    - Roark's Formulas for Stress and Strain (Composite Beam Sections)
    - Steiner's Parallel Axis Theorem for T-Sections / Ribbed Plates
    - Eurocode 3 / AISC Stiffness Deflection Criteria (delta <= L / 250)
    - Composite Design Handbook / MIL-HDBK-17 (Formability Bend Radius)
    """
    results: List[CheckResult] = []
    
    # 1. Composite Cross-Section Moment of Inertia via Steiner's Parallel Axis Theorem
    # Flange plate:
    a_flange = width_mm * thickness_mm
    y_flange = thickness_mm / 2.0
    i_flange_0 = (width_mm * (thickness_mm ** 3)) / 12.0
    
    # Gusset rib(s):
    h_rib = gusset_depth_mm if gusset_depth_mm > 0 else max(length_mm * 0.5, 10.0)
    t_rib = gusset_thickness_mm
    n_ribs = max(gusset_count, 0)
    
    if n_ribs > 0 and t_rib > 0 and h_rib > 0:
        a_rib_each = t_rib * h_rib
        y_rib = thickness_mm + (h_rib / 2.0)
        i_rib_0_each = (t_rib * (h_rib ** 3)) / 12.0
        
        a_total = a_flange + (n_ribs * a_rib_each)
        # Neutral axis centroid from bottom outer face of flange:
        y_centroid = (a_flange * y_flange + n_ribs * a_rib_each * y_rib) / a_total
        
        # Parallel axis summation: I_eff = sum(I_0 + A * d^2)
        i_eff = (
            (i_flange_0 + a_flange * ((y_flange - y_centroid) ** 2))
            + n_ribs * (i_rib_0_each + a_rib_each * ((y_rib - y_centroid) ** 2))
        )
        c_max = max(y_centroid, (thickness_mm + h_rib) - y_centroid)
    else:
        a_total = a_flange
        y_centroid = y_flange
        i_eff = i_flange_0
        c_max = y_flange

    # Bending moment at root: M = F * L
    m_bend = load_n * length_mm
    sigma_b = (m_bend * c_max) / max(i_eff, 1e-4)
    
    ms_bend = compute_margin_of_safety(applied=sigma_b, allowable=material.yield_strength_mpa, fos=fos)
    status_bend = evaluate_status(ms_bend)
    results.append(CheckResult(
        name="Cantilever Bending Stress (Steiner I_eff)",
        applied=round(sigma_b, 1),
        allowable=round(material.yield_strength_mpa, 1),
        margin_of_safety=round(ms_bend, 3),
        unit="MPa",
        status=status_bend,
        rule_ref="Steiner Theorem / Roark Bending",
        message=f"Root flexural stress (I_eff={i_eff:.0f} mm^4, c={c_max:.1f} mm, N_ribs={n_ribs})."
    ))
    
    # 2. Cantilever Tip Deflection Stiffness (delta <= L / 250)
    # delta = (F * L^3) / (3 * E * I_eff)
    e_mpa = material.elastic_modulus_gpa * 1000.0
    tip_deflection_mm = (load_n * (length_mm ** 3)) / (3.0 * e_mpa * max(i_eff, 1e-4))
    allowable_deflection_mm = length_mm / 250.0
    
    ms_deflection = compute_margin_of_safety(applied=tip_deflection_mm, allowable=allowable_deflection_mm, fos=1.0)
    status_deflection = evaluate_status(ms_deflection)
    results.append(CheckResult(
        name="Tip Deflection Stiffness (delta <= L/250)",
        applied=round(tip_deflection_mm, 2),
        allowable=round(allowable_deflection_mm, 2),
        margin_of_safety=round(ms_deflection, 3),
        unit="mm",
        status=status_deflection,
        rule_ref="Eurocode / AISC Deflection Limit",
        message=f"Cantilever tip deflection under load (E={e_mpa / 1000.0:.0f} GPa, allowable={allowable_deflection_mm:.2f} mm)."
    ))

    # 3. Composite / Sheet Metal Bend Radius Rule: R_in / t >= 1.5
    r_t_ratio = inner_radius_mm / max(thickness_mm, 0.1)
    results.append(CheckResult(
        name="Inner Bend Radius (R_in / t)",
        status=MarginStatus.POSITIVE if r_t_ratio >= 1.5 else (MarginStatus.LOW if r_t_ratio >= 1.0 else MarginStatus.NEGATIVE),
        margin_of_safety=round((r_t_ratio / 1.5) - 1.0, 2),
        applied=round(r_t_ratio, 2),
        allowable=1.5,
        unit="ratio",
        rule_ref="Composite Design Handbook / MIL-HDBK-17",
        message="Composite & metal formability guideline: R_in/t >= 1.5 prevents root delamination/cracking."
    ))
    
    return results
