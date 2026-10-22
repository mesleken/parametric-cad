"""Tests for safe AST-based constraint evaluator."""

import pytest
from pcad.domain.constraints import check_constraint

def test_safe_arithmetic_constraints():
    params = {"pcd": 90.0, "d_bolt": 12.0, "od": 120.0, "id": 40.0}
    
    # Valid condition
    ok, err = check_constraint("pcd + d_bolt < od", params)
    assert ok is True
    assert err is None
    
    # Invalid condition
    ok, err = check_constraint("pcd + 40.0 < od", params)
    assert ok is False
    assert "evaluated to False" in err

def test_safe_division_and_multiplication():
    params = {"w": 40.0, "d": 12.0, "e": 24.0}
    ok, err = check_constraint("e > (d / 2.0)", params)
    assert ok is True
    
    ok, err = check_constraint("w >= 2.0 * d", params)
    assert ok is True

def test_rejection_of_unsafe_nodes():
    params = {"a": 10.0}
    # Function calls, imports, eval should fail safely
    ok, err = check_constraint("__import__('os').system('dir')", params)
    assert ok is False
    assert "Unsupported AST node" in err
