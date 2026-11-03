"""Template registry and auto-discovery engine."""

import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Optional
from pcad.core.paths import get_user_templates_dir
from pcad.domain.errors import TemplateNotFoundError
from pcad.domain.template import TemplateSpec

class TemplateRegistry:
    _instance: Optional["TemplateRegistry"] = None
    _templates: Dict[str, TemplateSpec] = {}

    def __init__(self):
        self._templates = {}
        self.reload()

    def reload(self):
        """Reloads all built-in and user-promoted templates."""
        self._templates.clear()
        self._register_builtins()
        self._register_user_templates()

    def _register_builtins(self):
        builtin_modules = [
            "pcad.templates.builtin.demo.flange",
            "pcad.templates.builtin.aero.lug",
            "pcad.templates.builtin.aero.clevis",
            "pcad.templates.builtin.aero.gusset_bracket",
            "pcad.templates.builtin.aero.splice_plate",
            "pcad.templates.builtin.mech.stepped_shaft",
            "pcad.templates.builtin.mech.spur_gear",
            "pcad.templates.builtin.mech.enclosure",
        ]
        for mod_name in builtin_modules:
            try:
                mod = importlib.import_module(mod_name)
                for _, obj in inspect.getmembers(mod):
                    if isinstance(obj, TemplateSpec):
                        self._templates[obj.id] = obj
                    elif hasattr(obj, "_pcad_template_spec"):
                        spec = getattr(obj, "_pcad_template_spec")
                        self._templates[spec.id] = spec
            except Exception as e:
                import sys
                sys.stderr.write(f"[Warning] Failed to load built-in template {mod_name}: {e}\n")

    def _register_user_templates(self):
        user_dir = get_user_templates_dir()
        if not user_dir.exists():
            return
            
        for py_file in user_dir.glob("*.py"):
            try:
                mod_name = f"pcad_user_{py_file.stem}"
                spec = importlib.util.spec_from_file_location(mod_name, str(py_file))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    for _, obj in inspect.getmembers(mod):
                        if isinstance(obj, TemplateSpec):
                            self._templates[obj.id] = obj
                        elif hasattr(obj, "_pcad_template_spec"):
                            tpl_spec = getattr(obj, "_pcad_template_spec")
                            self._templates[tpl_spec.id] = tpl_spec
            except Exception as e:
                import sys
                sys.stderr.write(f"[Warning] Failed to load user template {py_file.name}: {e}\n")

    @classmethod
    def get_default_registry(cls) -> "TemplateRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def list_templates(self) -> List[TemplateSpec]:
        return list(self._templates.values())

    def get(self, template_id: str) -> TemplateSpec:
        if template_id not in self._templates:
            raise TemplateNotFoundError("err.template_not_found", f"Template '{template_id}' is not registered.")
        return self._templates[template_id]

    def register(self, spec: TemplateSpec) -> None:
        self._templates[spec.id] = spec
