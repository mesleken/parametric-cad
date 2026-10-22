"""Unit tests for engineering formulas and margins of safety."""

import pytest
from pcad.domain.materials import MaterialDB
from pcad.domain.template import MarginStatus
from pcad.engineering.margins import calc_margin_of_safety, evaluate_status
from pcad.engineering.lug import check_lug

def test_margin_of_safety_equation():
    # 1. Positive margin: allowable = 300, applied = 100, fos = 1.5 -> MS = 1.0
    ms_pos = calc_margin_of_safety(allowable=300.0, applied=100.0, fos=1.5)
    assert pytest.approx(ms_pos, 0.001) == 1.0
    assert evaluate_status(ms_pos) == MarginStatus.POSITIVE
    
    # 2. Critical zero margin: allowable = 300, applied = 200, fos = 1.5 -> MS = 0.0
    ms_crit = calc_margin_of_safety(allowable=300.0, applied=200.0, fos=1.5)
    assert pytest.approx(ms_crit, 0.001) == 0.0
    assert evaluate_status(ms_crit) == MarginStatus.LOW
    
    # 3. Negative margin: allowable = 300, applied = 250, fos = 1.5 -> MS = -0.2
    ms_neg = calc_margin_of_safety(allowable=300.0, applied=250.0, fos=1.5)
    assert pytest.approx(ms_neg, 0.001) == -0.2
    assert evaluate_status(ms_neg) == MarginStatus.NEGATIVE

def test_lug_hand_calculation_matching():
    """Validates straight lug stress calculations against analytical textbook hand calculation."""
    mat_db = MaterialDB.get_default_db()
    mat = mat_db.get("Al7075-T6") # Ftu = 572, Fbru = 1020, Fsu = 331
    
    # Dimensions: W = 40 mm, D = 10 mm, e = 20 mm, t = 5 mm, F = 6000 N, FoS = 1.5
    W, D, e, t, F = 40.0, 10.0, 20.0, 5.0, 6000.0
    checks = check_lug(W=W, D=D, e=e, t=t, F_axial_N=F, material=mat, K_tu=1.0, fos=1.5)
    
    # 1. Net tension: sigma = 6000 / ((40 - 10) * 5) = 40.0 MPa
    net_chk = next(c for c in checks if c.name == "Net-Section Tension")
    assert pytest.approx(net_chk.applied, 0.01) == 40.0
    # MS = 572 / (1.5 * 40.0) - 1 = 9.533 - 1 = 8.533
    assert pytest.approx(net_chk.margin_of_safety, 0.05) == 8.53
    
    # 2. Bearing: sigma = 6000 / (10 * 5) = 120.0 MPa
    brg_chk = next(c for c in checks if c.name == "Pin Bearing Stress")
    assert pytest.approx(brg_chk.applied, 0.01) == 120.0
    # MS = 1020 / (1.5 * 120.0) - 1 = 5.667 - 1 = 4.67
    assert pytest.approx(brg_chk.margin_of_safety, 0.05) == 4.67
    
    # 3. Shear Tear-out: tau = 6000 / (2 * (20 - 5) * 5) = 40.0 MPa
    tear_chk = next(c for c in checks if c.name == "Shear Tear-Out")
    assert pytest.approx(tear_chk.applied, 0.01) == 40.0
    # MS = 331 / (1.5 * 40.0) - 1 = 5.517 - 1 = 4.52
    assert pytest.approx(tear_chk.margin_of_safety, 0.05) == 4.52
    
    # 4. Aerospace ratio rules
    ed_chk = next(c for c in checks if "e / D" in c.name)
    assert ed_chk.applied == 2.0 # 20 / 10 = 2.0 >= 1.5
    assert ed_chk.status == MarginStatus.POSITIVE
