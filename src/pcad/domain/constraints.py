"""Safe AST-based mathematical and relational expression evaluator for template constraints.

Evaluates expressions like 'bolt_circle + bolt_hole_dia < outer_dia' without eval().
Only allows safe arithmetic (+, -, *, /, //, %, **) and comparisons (<, <=, >, >=, ==, !=).
"""

import ast
import operator
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel

class ConstraintRule(BaseModel):
    expr: str
    message: Dict[str, str] # e.g. {"en": "...", "tr": "..."}
    field: Optional[str] = None # associated field to highlight

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}

def evaluate_safe_expression(node: ast.AST, variables: Dict[str, Any]) -> Any:
    """Recursively evaluates an AST node strictly restricted to safe math and variables."""
    if isinstance(node, ast.Expression):
        return evaluate_safe_expression(node.body, variables)
    
    elif isinstance(node, ast.Constant): # Numbers, booleans, strings in Py3.8+
        return node.value
        
    elif isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        raise ValueError(f"Unknown variable in constraint: '{node.id}'")
        
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = evaluate_safe_expression(node.operand, variables)
        return SAFE_OPERATORS[op_type](operand)
        
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        left = evaluate_safe_expression(node.left, variables)
        right = evaluate_safe_expression(node.right, variables)
        return SAFE_OPERATORS[op_type](left, right)
        
    elif isinstance(node, ast.Compare):
        left = evaluate_safe_expression(node.left, variables)
        for op, comparator in zip(node.ops, node.comparators):
            op_type = type(op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported comparison operator: {op_type.__name__}")
            right = evaluate_safe_expression(comparator, variables)
            if not SAFE_OPERATORS[op_type](left, right):
                return False
            left = right
        return True
        
    else:
        raise ValueError(f"Unsupported AST node in constraint expression: {type(node).__name__}")

def check_constraint(expr_str: str, variables: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Evaluates constraint string against parameters.
    
    Returns (True, None) if condition is satisfied, or (False, error_detail) if violated.
    """
    try:
        parsed = ast.parse(expr_str, mode="eval")
        result = evaluate_safe_expression(parsed, variables)
        if bool(result):
            return True, None
        return False, f"Constraint expression '{expr_str}' evaluated to False."
    except Exception as e:
        return False, f"Evaluation error in '{expr_str}': {e}"
