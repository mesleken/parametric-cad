"""Flange geometric rule and ASME Section VIII pressure checks."""

import math
from typing import List, Optional
from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus
from pcad.engineering.margins import compute_margin_of_safety, evaluate_status

def check_flange(
    outer_dia: float,
    inner_dia: float,
    pcd: float,
    num_bolts: int,
    bolt_hole_dia: float,
    flange_thickness: float,
    neck_outer_dia: float = 0.0,
    neck_height: float = 0.0,
    design_pressure_mpa: float = 1.6,
    material: Optional[Material] = None,
    fos: float = 1.5,
    **kwargs
) -> List[CheckResult]:
    """Evaluates bolt ligament clearance, outer edge distance, ASME Section VIII 
    hydrostatic bolt tensile stress, and hub hoop stress under internal pressure.
    
    References:
    - ASME Section VIII Division 1, Appendix 2 (Rules for Bolted Flange Connections)
    - EN 13445-3 (Unfired Pressure Vessels - Flanges)
    - DIN 2501 / ASME B16.5 (Standard Flange Proportions & Wrench Clearance)
    """
    results: List[CheckResult] = []
    
    # 1. Bolt-to-bolt chord distance (Ligament)
    angle_rad = (2.0 * math.pi) / max(num_bolts, 1)
    chord_pitch = pcd * math.sin(angle_rad / 2.0)
    ligament = chord_pitch - bolt_hole_dia
    min_required_ligament = 1.0 * bolt_hole_dia
    ms_ligament = compute_margin_of_safety(applied=min_required_ligament, allowable=ligament, fos=1.0)
    results.append(CheckResult(
        name="Bolt-to-Bolt Ligament",
        status=MarginStatus.POSITIVE if ms_ligament >= 0.0 else MarginStatus.NEGATIVE,
        margin_of_safety=round(ms_ligament, 2),
        applied=round(ligament, 2),
        allowable=round(min_required_ligament, 2),
        unit="mm",
        rule_ref="DIN 2501 / ASME B16.5 Clearance Rule",
        message="Web thickness between adjacent bolt holes for socket/wrench clearance."
    ))
    
    # 2. Outer Edge Distance: (OD - PCD) / 2
    outer_edge_dist = (outer_dia - pcd) / 2.0
    min_outer_edge = 1.25 * bolt_hole_dia
    ms_edge = compute_margin_of_safety(applied=min_outer_edge, allowable=outer_edge_dist, fos=1.0)
    results.append(CheckResult(
        name="Outer Edge Distance",
        status=MarginStatus.POSITIVE if ms_edge >= 0.0 else MarginStatus.NEGATIVE,
        margin_of_safety=round(ms_edge, 2),
        applied=round(outer_edge_dist, 2),
        allowable=round(min_outer_edge, 2),
        unit="mm",
        rule_ref="ASME B16.5 Bolted Joint Margin",
        message="Flange outer rim width to prevent edge tear-out."
    ))
    
    # 3. ASME Section VIII Appendix 2: Hydrostatic End Force & Bolt Tensile Stress
    # Effective gasket / reaction diameter G ~= (PCD + inner_dia) / 2
    g_dia = (pcd + inner_dia) / 2.0
    # Hydrostatic end force: H = (pi / 4) * G^2 * P
    h_force_n = (math.pi / 4.0) * (g_dia ** 2) * design_pressure_mpa
    
    # Fastener tensile stress area (ISO metric coarse pitch approx: At ~= 0.78 * (0.85 * d)^2)
    nominal_bolt_dia = max(bolt_hole_dia - 1.0, 3.0)
    a_bolt_tensile = (math.pi / 4.0) * ((0.85 * nominal_bolt_dia) ** 2)
    total_bolt_area = max(num_bolts, 1) * a_bolt_tensile
    sigma_bolt = h_force_n / total_bolt_area
    
    # Allowable bolt stress (ASTM A193 B7 / Grade 8.8 flange stud allowable ~= 250 MPa)
    allowable_bolt = 250.0
    ms_bolt = compute_margin_of_safety(applied=sigma_bolt, allowable=allowable_bolt, fos=fos)
    status_bolt = evaluate_status(ms_bolt)
    results.append(CheckResult(
        name="ASME VIII Bolt Tensile Stress",
        applied=round(sigma_bolt, 1),
        allowable=allowable_bolt,
        margin_of_safety=round(ms_bolt, 3),
        unit="MPa",
        status=status_bolt,
        rule_ref="ASME Sec VIII App. 2 (Eq. 2-3)",
        message=f"Hydrostatic end force H={h_force_n / 1000.0:.1f} kN at P={design_pressure_mpa:.1f} MPa across {num_bolts} bolts."
    ))
    
    # 4. Hub / Neck Hoop Stress Check
    effective_neck_od = neck_outer_dia if neck_outer_dia > inner_dia else outer_dia * 0.7
    neck_thickness = (effective_neck_od - inner_dia) / 2.0
    if neck_thickness > 0:
        sigma_hoop = (design_pressure_mpa * inner_dia) / (2.0 * neck_thickness)
        yield_str = material.yield_strength_mpa if material else 250.0
        # ASME Section VIII design allowable stress Sm = 2/3 * Sy
        sm_allowable = (2.0 / 3.0) * yield_str
        ms_hoop = compute_margin_of_safety(applied=sigma_hoop, allowable=sm_allowable, fos=fos)
        status_hoop = evaluate_status(ms_hoop)
        results.append(CheckResult(
            name="Hub Hoop Stress (sigma_h)",
            applied=round(sigma_hoop, 1),
            allowable=round(sm_allowable, 1),
            margin_of_safety=round(ms_hoop, 3),
            unit="MPa",
            status=status_hoop,
            rule_ref="ASME Sec VIII Div 1 / EN 13445",
            message=f"Circumferential hoop stress in weld-neck wall (t={neck_thickness:.1f} mm) under {design_pressure_mpa} MPa."
        ))

    return results
