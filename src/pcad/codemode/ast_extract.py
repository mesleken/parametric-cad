"""AST-based script analysis for Mod 3: Code-to-Template extraction."""

import ast
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple
import platformdirs

class ExtractedParam(tuple):
    def __new__(cls, name: str, default: Any, type_str: str, func_name: str = "custom_part"):
        return super().__new__(cls, (name, default, type_str))

    @property
    def name(self) -> str:
        return self[0]

    @property
    def default(self) -> Any:
        return self[1]

    @property
    def type(self) -> str:
        return self[2]

    def __getitem__(self, item):
        if isinstance(item, str):
            if item == "name":
                return self[0]
            elif item in ("default", "val"):
                return self[1]
            elif item == "type":
                return self[2]
            elif item == "func_name":
                return "custom_part"
            raise KeyError(item)
        return super().__getitem__(item)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

def extract_parameters_from_ast(code_str: str) -> List[ExtractedParam]:
    """Analyzes Python code AST and extracts parameters from top-level assignments or function signatures."""
    tree = ast.parse(code_str)
    params: List[ExtractedParam] = []
    
    # 1. First check if there is a function definition with default arguments
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            args = node.args.args
            defaults = node.args.defaults
            num_defaults = len(defaults)
            for i, arg_node in enumerate(args):
                arg_name = arg_node.arg
                default_idx = i - (len(args) - num_defaults)
                if default_idx >= 0:
                    def_expr = defaults[default_idx]
                    val = def_expr.value if isinstance(def_expr, ast.Constant) else 0.0
                else:
                    val = 10.0
                val_type = "float" if isinstance(val, float) else ("int" if isinstance(val, int) else "str")
                params.append(ExtractedParam(arg_name, val, val_type, node.name))
            if params:
                return params

    # 2. Otherwise extract top-level variable assignments
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    if isinstance(node.value, ast.Constant):
                        val = node.value.value
                        val_type = "float" if isinstance(val, float) else ("int" if isinstance(val, int) else "str")
                        params.append(ExtractedParam(var_name, val, val_type, "custom_part"))
    return params

def promote_script_to_template(
    code_str: str,
    template_id: str,
    template_name: str,
    category: str = "User Custom",
    description: str = "Custom template automatically promoted from Python script."
) -> Path:
    """Converts a user script into a valid pcad template file and registers it."""
    params = extract_parameters_from_ast(code_str)
    if not params:
        raise ValueError("No parameter variables or function arguments found in script (e.g. width = 40.0).")
        
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", template_id.lower())
    
    # Generate Pydantic parameter class code
    fields_code = []
    for p in params:
        name = p["name"]
        val = p["default"]
        vtype = p["type"]
        fields_code.append(f"    {name}: {vtype} = {val}")
        
    param_block = "\n".join(fields_code)
    
    # Body replacement: replace literal assignment with p.<name>
    body_lines = []
    param_names = {p["name"] for p in params}
    for line in code_str.splitlines():
        # Skip original assignments of the extracted parameters
        stripped = line.strip()
        matched = False
        for p_name in param_names:
            if stripped.startswith(f"{p_name} =") or stripped.startswith(f"{p_name}="):
                matched = True
                break
        if not matched:
            # Replace variable usages with params.<name>
            modified_line = line
            for p_name in param_names:
                # regex word boundary replace
                modified_line = re.sub(rf"\b{p_name}\b", f"params.{p_name}", modified_line)
            body_lines.append("    " + modified_line)
            
    body_block = "\n".join(body_lines)
    
    template_content = f'''"""User-generated template: {template_name}"""

from pydantic import BaseModel
from pcad.domain.template import template

class CustomParams_{slug}(BaseModel):
{param_block}

@template(
    id="user.{slug}",
    version="1.0.0",
    category="{category}",
    name="{template_name}",
    description="{description}",
    params=CustomParams_{slug}
)
def build(params: CustomParams_{slug}):
{body_block}
    return result
'''
    
    # Save to user templates directory
    user_tpl_dir = Path(platformdirs.user_data_dir("pcad", "pcad")) / "templates"
    user_tpl_dir.mkdir(parents=True, exist_ok=True)
    out_file = user_tpl_dir / f"user_{slug}.py"
    
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(template_content)
        
    return out_file
