"""AST-based script analysis for Mod 3: Code-to-Template extraction."""

import ast
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
from pcad.core.paths import get_user_templates_dir

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
                # Infer type annotation if present
                if arg_node.annotation and isinstance(arg_node.annotation, ast.Name):
                    val_type = arg_node.annotation.id
                else:
                    val_type = "float" if isinstance(val, float) else ("int" if isinstance(val, int) else ("bool" if isinstance(val, bool) else "str"))
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
                        val_type = "float" if isinstance(val, float) else ("int" if isinstance(val, int) else ("bool" if isinstance(val, bool) else "str"))
                        params.append(ExtractedParam(var_name, val, val_type, "custom_part"))
    return params

def promote_script_to_template(
    code_str: str,
    template_id: str,
    template_name: str,
    category: str = "User Custom",
    description: str = "Custom template automatically promoted from Python script.",
    param_overrides: Optional[List[Dict[str, Any]]] = None
) -> Path:
    """Converts a user script into a valid pcad template file and registers it."""
    if param_overrides:
        params_data = param_overrides
    else:
        raw_params = extract_parameters_from_ast(code_str)
        if not raw_params:
            raise ValueError("No parameter variables or function arguments found in script (e.g. width = 40.0).")
        params_data = [
            {"name": p["name"], "default": p["default"], "type": p["type"], "unit": "mm" if p["type"] == "float" else "-"}
            for p in raw_params
        ]
        
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", template_id.lower())
    
    # Generate Pydantic parameter class code with Annotated, Field, and UI metadata
    fields_code = []
    for p in params_data:
        name = p["name"]
        val = p["default"]
        vtype = p.get("type", "float")
        unit = p.get("unit", "mm" if vtype == "float" else "-")
        min_val = p.get("min", None)
        max_val = p.get("max", None)
        
        field_args = []
        if min_val is not None and vtype in ("float", "int"):
            field_args.append(f"ge={min_val}")
        if max_val is not None and vtype in ("float", "int"):
            field_args.append(f"le={max_val}")
        field_clause = f"Field({', '.join(field_args)})" if field_args else "Field()"
        
        if vtype == "str":
            val_repr = repr(str(val))
        elif vtype == "bool":
            val_repr = str(bool(val))
        elif vtype == "int":
            val_repr = str(int(val))
        elif vtype == "float":
            val_repr = str(float(val))
        else:
            val_repr = repr(val)
        
        label_str = name.replace("_", " ").title()
        ui_clause = f'UI(label="{label_str}", unit="{unit}")'
        fields_code.append(f"    {name}: Annotated[{vtype}, {field_clause}, {ui_clause}] = {val_repr}")
        
    param_class_src = "\n".join(fields_code)
    
    param_class_name = f"CustomParams_{slug}"
    
    # Check if code has a function or is a sequential script
    has_func = any(isinstance(node, ast.FunctionDef) for node in ast.parse(code_str).body)
    
    if has_func:
        # Wrap the function call
        fn_match = re.search(r"def\s+([a-zA-Z0-9_]+)\s*\(", code_str)
        fn_name = fn_match.group(1) if fn_match else "build_part"
        kwargs_pass = ", ".join([f"{p['name']}=params.{p['name']}" for p in params_data])
        exec_body = f"""
{code_str}

@template(
    id="user.{slug}",
    version="1.0.0",
    category="{category}",
    name="{template_name}",
    description="{description}",
    params={param_class_name},
    default_material="Al7075-T6"
)
def build(params: {param_class_name}):
    return {fn_name}({kwargs_pass})
"""
    else:
        # Sequential script: replace parameter assignments with params.<param>
        body_lines = []
        for line in code_str.splitlines():
            is_param_line = False
            for p in params_data:
                name = p["name"]
                if re.match(rf"^\s*{name}\s*=", line):
                    body_lines.append(f"    {name} = params.{name}")
                    is_param_line = True
                    break
            if not is_param_line:
                body_lines.append(f"    {line}")
                
        indented_body = "\n".join(body_lines)
        exec_body = f"""
@template(
    id="user.{slug}",
    version="1.0.0",
    category="{category}",
    name="{template_name}",
    description="{description}",
    params={param_class_name},
    default_material="Al7075-T6"
)
def build(params: {param_class_name}):
{indented_body}
    return result if 'result' in locals() else (part if 'part' in locals() else None)
"""

    file_content = f'''"""User Created Parametric CAD Template: {template_name}"""
from typing import Annotated, List
from pydantic import BaseModel, Field
import build123d as bd
from pcad.domain.template import UI, template

class {param_class_name}(BaseModel):
{param_class_src}

{exec_body}
'''
    user_tpl_dir = get_user_templates_dir()
    user_tpl_dir.mkdir(parents=True, exist_ok=True)
    out_file = user_tpl_dir / f"{slug}.py"
    out_file.write_text(file_content, encoding="utf-8")
    return out_file
