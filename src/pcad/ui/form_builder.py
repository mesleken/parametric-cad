"""Schema-driven dynamic form generation using PySide6."""

from typing import Any, Dict, Optional, Type
from PySide6 import QtCore, QtWidgets
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from pcad.domain.i18n import t
from pcad.domain.template import UI

class SchemaFormWidget(QtWidgets.QWidget):
    values_changed = Signal = QtCore.Signal(dict)

    def __init__(self, param_cls: Optional[Type[BaseModel]] = None, parent=None):
        super().__init__(parent)
        self._param_cls = param_cls
        self._widgets: Dict[str, QtWidgets.QWidget] = {}
        self._groups: Dict[str, QtWidgets.QGroupBox] = {}
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(8)
        
        # Scroll area for long parameter lists
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        self.container = QtWidgets.QWidget()
        self.container_layout = QtWidgets.QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(10)
        
        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)
        
        # Inline validation feedback banner
        self.error_banner = QtWidgets.QLabel(self)
        self.error_banner.setWordWrap(True)
        self.error_banner.setStyleSheet(
            "background: #FFF5F5; color: #C53030; border: 1px solid #FEB2B2; "
            "border-radius: 4px; padding: 6px; font-size: 11px; font-weight: bold;"
        )
        self.error_banner.setVisible(False)
        main_layout.addWidget(self.error_banner)
        
        if param_cls:
            self.build_form(param_cls)

    def build_form(self, param_cls: Type[BaseModel]):
        self.blockSignals(True)
        try:
            self._param_cls = param_cls
            self._widgets.clear()
            self._groups.clear()
            
            # Clear existing layout
            while self.container_layout.count():
                item = self.container_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            group_layouts: Dict[str, QtWidgets.QFormLayout] = {}

            for field_name, field_info in param_cls.model_fields.items():
                ui_meta = self._extract_ui_meta(field_info)
                group_name = ui_meta.group if ui_meta else "geometry"
                group_title = t(f"group.{group_name}")
                
                # Create group if not existing
                if group_name not in self._groups:
                    grp_box = QtWidgets.QGroupBox(group_title, self.container)
                    grp_layout = QtWidgets.QFormLayout(grp_box)
                    grp_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
                    grp_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
                    self._groups[group_name] = grp_box
                    group_layouts[group_name] = grp_layout
                    self.container_layout.addWidget(grp_box)
                    
                form_layout = group_layouts[group_name]
                widget = self._create_field_widget(field_name, field_info, ui_meta)
                self._widgets[field_name] = widget
                
                # Label
                label_text = t(ui_meta.label) if (ui_meta and ui_meta.label) else field_name.replace("_", " ").title()
                form_layout.addRow(label_text, widget)
                
            self.container_layout.addStretch()
            self._clear_field_errors()
            self.error_banner.setVisible(False)
        finally:
            self.blockSignals(False)

    def _extract_ui_meta(self, field_info: FieldInfo) -> Optional[UI]:
        for meta in field_info.metadata:
            if isinstance(meta, UI):
                return meta
        return None

    def _create_field_widget(self, name: str, field_info: FieldInfo, ui_meta: Optional[UI]) -> QtWidgets.QWidget:
        annotation = field_info.annotation
        default_val = field_info.default if field_info.default is not None else 0
        
        unit = ui_meta.unit if ui_meta else ""
        step = ui_meta.step if ui_meta else 1.0
        
        # Numeric float
        if annotation is float or annotation == float:
            sb = QtWidgets.QDoubleSpinBox(self.container)
            sb.setRange(-1e7, 1e7)
            sb.setDecimals(2)
            sb.setSingleStep(step)
            if unit and unit != "-":
                sb.setSuffix(f" {unit}")
            sb.setValue(float(default_val))
            sb.valueChanged.connect(self._on_any_value_changed)
            return sb
            
        # Integer
        elif annotation is int or annotation == int:
            sb = QtWidgets.QSpinBox(self.container)
            sb.setRange(-1000000, 1000000)
            sb.setSingleStep(int(step))
            if unit and unit != "-":
                sb.setSuffix(f" {unit}")
            sb.setValue(int(default_val))
            sb.valueChanged.connect(self._on_any_value_changed)
            return sb
            
        # Boolean
        elif annotation is bool or annotation == bool:
            cb = QtWidgets.QCheckBox(self.container)
            cb.setChecked(bool(default_val))
            cb.toggled.connect(self._on_any_value_changed)
            return cb
            
        # Choices or String
        elif ui_meta and ui_meta.choices:
            combo = QtWidgets.QComboBox(self.container)
            combo.addItems(ui_meta.choices)
            if str(default_val) in ui_meta.choices:
                combo.setCurrentText(str(default_val))
            combo.currentTextChanged.connect(self._on_any_value_changed)
            return combo
            
        else:
            line = QtWidgets.QLineEdit(str(default_val), self.container)
            line.textChanged.connect(self._on_any_value_changed)
            return line

    def _on_any_value_changed(self, *args):
        values = self.get_values()
        if self._param_cls:
            try:
                self._param_cls(**values)
                self._clear_field_errors()
                self.error_banner.setVisible(False)
                self.values_changed.emit(values)
            except Exception as e:
                # Format friendly message from pydantic error
                err_text = str(e)
                first_line = err_text.splitlines()[0]
                if "Value error," in err_text:
                    for line in err_text.splitlines():
                        if "Value error," in line:
                            first_line = line.replace("Value error,", "").strip()
                            break
                elif "Input should be" in err_text:
                    for line in err_text.splitlines():
                        if "Input should be" in line:
                            first_line = line.strip()
                            break
                self.error_banner.setText(f"⚠️ {first_line}")
                self.error_banner.setVisible(True)
                self._highlight_field_error(err_text)
        else:
            self.values_changed.emit(values)

    def _clear_field_errors(self):
        for w in self._widgets.values():
            w.setStyleSheet("")

    def _highlight_field_error(self, err_text: str):
        # Match field names mentioned in error text
        for name, widget in self._widgets.items():
            if name in err_text:
                widget.setStyleSheet("border: 1px solid #E53E3E; background: #FFF5F5;")

    def get_values(self) -> Dict[str, Any]:
        values = {}
        for name, widget in self._widgets.items():
            if isinstance(widget, QtWidgets.QDoubleSpinBox):
                values[name] = float(widget.value())
            elif isinstance(widget, QtWidgets.QSpinBox):
                values[name] = int(widget.value())
            elif isinstance(widget, QtWidgets.QCheckBox):
                values[name] = bool(widget.isChecked())
            elif isinstance(widget, QtWidgets.QComboBox):
                values[name] = widget.currentText()
            elif isinstance(widget, QtWidgets.QLineEdit):
                values[name] = widget.text()
        return values

    def set_values(self, values: Dict[str, Any]):
        self.blockSignals(True)
        for name, val in values.items():
            if name in self._widgets:
                w = self._widgets[name]
                if isinstance(w, QtWidgets.QDoubleSpinBox):
                    w.setValue(float(val))
                elif isinstance(w, QtWidgets.QSpinBox):
                    w.setValue(int(val))
                elif isinstance(w, QtWidgets.QCheckBox):
                    w.setChecked(bool(val))
                elif isinstance(w, QtWidgets.QComboBox):
                    w.setCurrentText(str(val))
                elif isinstance(w, QtWidgets.QLineEdit):
                    w.setText(str(val))
        self.blockSignals(False)
        self.values_changed.emit(self.get_values())
