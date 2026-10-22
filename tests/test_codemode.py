"""Unit tests for Mod 3 AST parameter extraction and template generation."""

import pytest
from pcad.codemode.ast_extract import extract_parameters_from_ast, promote_script_to_template

SAMPLE_SCRIPT = '''import build123d as bd

# Parameters
width = 50.0
height = 30.0
thickness = 6.0

with bd.BuildPart() as p:
    bd.Box(width, height, thickness)

result = p.part
'''

def test_ast_parameter_extraction():
    params = extract_parameters_from_ast(SAMPLE_SCRIPT)
    param_dict = {p[0]: p[1] for p in params}
    assert "width" in param_dict
    assert param_dict["width"] == 50.0
    assert param_dict["height"] == 30.0
    assert param_dict["thickness"] == 6.0

def test_promote_script_generation(tmp_path):
    saved_file = promote_script_to_template(
        code_str=SAMPLE_SCRIPT,
        template_id="test_bracket",
        template_name="Test Bracket"
    )
    assert saved_file.exists()
    content = saved_file.read_text(encoding="utf-8")
    assert "class CustomParams_test_bracket(BaseModel):" in content
    assert "params.width" in content
    assert "id=\"user.test_bracket\"" in content
