"""Margin of Safety (MS) calculations and status evaluation."""

import math
from pcad.domain.template import CheckResult, MarginStatus

def calc_margin_of_safety(allowable: float, applied: float, fos: float = 1.5) -> float:
    """Computes Margin of Safety (MS).
    
    MS = Allowable / (FoS * Applied) - 1.0
    If applied <= 0, returns infinity (no applied load).
    """
    if applied <= 0.0 or math.isclose(applied, 0.0):
        return 999.0  # Represents infinite positive margin
    if fos <= 0.0:
        fos = 1.0
    return (allowable / (fos * applied)) - 1.0

compute_margin_of_safety = calc_margin_of_safety

def evaluate_status(margin: float) -> MarginStatus:
    if margin < 0.0:
        return MarginStatus.NEGATIVE
    elif margin < 0.10:
        return MarginStatus.LOW
    else:
        return MarginStatus.POSITIVE

def make_check_result(
    name: str,
    applied: float,
    allowable: float,
    fos: float = 1.5,
    unit: str = "MPa",
    rule_ref: str = "",
    message: str = ""
) -> CheckResult:
    ms = calc_margin_of_safety(allowable, applied, fos)
    status = evaluate_status(ms)
    return CheckResult(
        name=name,
        status=status,
        margin_of_safety=round(ms, 3) if ms < 900.0 else 999.0,
        applied=round(applied, 2),
        allowable=round(allowable, 2),
        unit=unit,
        fos=fos,
        rule_ref=rule_ref,
        message=message
    )
