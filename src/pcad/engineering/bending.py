"""Gusseted bracket / L-bracket flexural stress and composite corner radius checks."""

from typing import List
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus
from pcad.engineering.margins import make_check_result

def check_bracket(
    length_mm: float,
    width_mm: float,
    thickness_mm: float,
    inner_radius_mm: float,
    load_n: float,
    material: Material,
    gusset_count: int = 1,
    gusset_thickness_mm: float = 4.0,
    fos: float = 1.5
) -> List[CheckResult]:
    results: List[CheckResult] = []
    
    # 1. Cantilever bending stress at base
    # M = F * L
    m_bend = load_n * length_mm
    # Base plate moment of inertia: I_base = width * thickness^3 / 12
    # Plus gusset stiffener contribution
    i_base = (width_mm * (thickness_mm ** 3)) / 12.0
    c = thickness_mm / 2.0
    
    # Stiffener stiffness factor (1.5x with gussets)
    stiff_factor = 1.0 + (0.5 * gusset_count * (gusset_thickness_mm / max(thickness_mm, 1.0)))
    effective_i = i_base * stiff_factor
    
    sigma_b = (m_bend * c) / max(effective_i, 1e-4)
    results.append(make_check_result(
        name="Cantilever Bending Stress",
        applied=sigma_b,
        allowable=material.yield_strength_mpa,
        fos=fos,
        unit="MPa",
        rule_ref="Roark's Formulas for Stress and Strain",
        message="Maximum flexural stress at bracket base root"
    ))
    
    # 2. Composite / Sheet Metal Bend Radius Rule: R_in / t >= 1.5
    # For CFRP or bent aluminium, small bend radius causes microcracking/delamination
    r_t_ratio = inner_radius_mm / max(thickness_mm, 0.1)
    results.append(CheckResult(
        name="Inner Bend Radius (R_in / t)",
        status=MarginStatus.POSITIVE if r_t_ratio >= 1.5 else (MarginStatus.LOW if r_t_ratio >= 1.0 else MarginStatus.NEGATIVE),
        margin_of_safety=round((r_t_ratio / 1.5) - 1.0, 2),
        applied=round(r_t_ratio, 2),
        allowable=1.5,
        unit="ratio",
        rule_ref="Composite Design Handbook / MIL-HDBK-17",
        message="Composite & metal formability guideline: R_in/t >= 1.5 prevents root delamination"
    ))
    
    return results
