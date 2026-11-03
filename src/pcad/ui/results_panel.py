"""Results & Engineering Verification Panel."""

from typing import List, Optional
from PySide6 import QtCore, QtGui, QtWidgets

from pcad.domain.i18n import t
from pcad.domain.materials import Material, MaterialDB
from pcad.domain.template import CheckResult, MarginStatus, PhysicsResult

class ResultsPanel(QtWidgets.QWidget):
    material_changed = QtCore.Signal(str) # material_id

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        # Sub-tabs: 1. Margins & Physics, 2. Method & Theory
        self.sub_tabs = QtWidgets.QTabWidget(self)
        
        # Tab 1: Analysis
        tab_analysis = QtWidgets.QWidget()
        ana_layout = QtWidgets.QVBoxLayout(tab_analysis)
        ana_layout.setContentsMargins(4, 4, 4, 4)
        ana_layout.setSpacing(8)
        
        # 1. Material Selection Group
        mat_group = QtWidgets.QGroupBox(t("panel.materials"), tab_analysis)
        mat_layout = QtWidgets.QHBoxLayout(mat_group)
        self.combo_material = QtWidgets.QComboBox(mat_group)
        self._populate_materials()
        self.combo_material.currentTextChanged.connect(self._on_material_changed)
        mat_layout.addWidget(self.combo_material)
        ana_layout.addWidget(mat_group)
        
        # 2. Physical Properties Group
        phys_group = QtWidgets.QGroupBox(t("panel.physics"), tab_analysis)
        phys_layout = QtWidgets.QFormLayout(phys_group)
        phys_layout.setContentsMargins(8, 8, 8, 8)
        phys_layout.setSpacing(6)
        
        self.lbl_mass = QtWidgets.QLabel("—", phys_group)
        self.lbl_mass.setStyleSheet("font-weight: bold; color: #2B6CB0;")
        self.lbl_volume = QtWidgets.QLabel("—", phys_group)
        self.lbl_cog = QtWidgets.QLabel("—", phys_group)
        self.lbl_bbox = QtWidgets.QLabel("—", phys_group)
        self.lbl_inertia = QtWidgets.QLabel("—", phys_group)
        
        phys_layout.addRow("Mass (Kütle):", self.lbl_mass)
        phys_layout.addRow("Volume (Hacim):", self.lbl_volume)
        phys_layout.addRow("CoG (Ağırlık Merk.):", self.lbl_cog)
        phys_layout.addRow("BBox (Sınır Kutusu):", self.lbl_bbox)
        phys_layout.addRow("Inertia (Atalet):", self.lbl_inertia)
        ana_layout.addWidget(phys_group)
        
        # 3. Engineering Margins Table
        eng_group = QtWidgets.QGroupBox(t("panel.engineering"), tab_analysis)
        eng_layout = QtWidgets.QVBoxLayout(eng_group)
        eng_layout.setContentsMargins(6, 6, 6, 6)
        
        self.table_checks = QtWidgets.QTableWidget(0, 4, eng_group)
        self.table_checks.setHorizontalHeaderLabels(["Check Mode", "Applied", "MS", "Status"])
        self.table_checks.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table_checks.verticalHeader().setVisible(False)
        self.table_checks.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_checks.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        eng_layout.addWidget(self.table_checks)
        ana_layout.addWidget(eng_group)
        
        # 4. Disclaimer Footer
        self.lbl_disclaimer = QtWidgets.QLabel(t("disclaimer.engineering"), tab_analysis)
        self.lbl_disclaimer.setWordWrap(True)
        self.lbl_disclaimer.setStyleSheet("color: #718096; font-size: 10px; font-style: italic; border-top: 1px solid #E2E8F0; padding-top: 4px;")
        ana_layout.addWidget(self.lbl_disclaimer)
        
        self.sub_tabs.addTab(tab_analysis, t("tab.results_margins", default="Results && Margins"))
        
        # Tab 2: Method & Theory
        self.method_browser = QtWidgets.QTextBrowser()
        self.method_browser.setOpenExternalLinks(True)
        self.sub_tabs.addTab(self.method_browser, t("tab.method_theory", default="Method && Theory"))
        
        layout.addWidget(self.sub_tabs)

    def set_method_doc(self, title: str, doc_markdown: str):
        self.method_browser.setMarkdown(doc_markdown)

    def _populate_materials(self):
        mat_db = MaterialDB.get_default_db()
        for mat in mat_db.list_materials():
            self.combo_material.addItem(f"{mat.name} ({mat.density_g_cm3:.2f} g/cm³)", mat.id)

    def _on_material_changed(self, text: str):
        mat_id = self.combo_material.currentData()
        if mat_id:
            self.material_changed.emit(mat_id)

    def get_selected_material_id(self) -> str:
        return self.combo_material.currentData() or "Al7075-T6"

    def set_material_id(self, material_id: str):
        idx = self.combo_material.findData(material_id)
        if idx >= 0:
            self.combo_material.blockSignals(True)
            self.combo_material.setCurrentIndex(idx)
            self.combo_material.blockSignals(False)

    def update_physics(self, phys: PhysicsResult):
        self.lbl_mass.setText(f"{phys.mass_g:.1f} g ({phys.mass_g / 1000.0:.3f} kg)")
        self.lbl_volume.setText(f"{phys.volume_mm3:.1f} mm³")
        self.lbl_cog.setText(f"({phys.cog_mm[0]}, {phys.cog_mm[1]}, {phys.cog_mm[2]}) mm")
        dx = phys.bbox_mm[3] - phys.bbox_mm[0]
        dy = phys.bbox_mm[4] - phys.bbox_mm[1]
        dz = phys.bbox_mm[5] - phys.bbox_mm[2]
        self.lbl_bbox.setText(f"{dx:.1f} × {dy:.1f} × {dz:.1f} mm")
        self.lbl_inertia.setText(f"({phys.inertia_g_mm2[0]:.0f}, {phys.inertia_g_mm2[1]:.0f}, {phys.inertia_g_mm2[2]:.0f}) g·mm²")

    def update_checks(self, checks: List[CheckResult]):
        self.table_checks.setRowCount(len(checks))
        for row, chk in enumerate(checks):
            item_name = QtWidgets.QTableWidgetItem(chk.name)
            item_name.setToolTip(f"Ref: {chk.rule_ref}\n{chk.message}")
            
            item_applied = QtWidgets.QTableWidgetItem(f"{chk.applied} {chk.unit}")
            
            ms_val = chk.margin_of_safety
            ms_text = f"+{ms_val:.2f}" if (ms_val > 0 and ms_val < 900) else (f"{ms_val:.2f}" if ms_val < 900 else "+Inf")
            item_ms = QtWidgets.QTableWidgetItem(ms_text)
            item_ms.setTextAlignment(QtCore.Qt.AlignCenter)
            
            item_status = QtWidgets.QTableWidgetItem(chk.status.value)
            item_status.setTextAlignment(QtCore.Qt.AlignCenter)
            
            # Color code status
            if chk.status == MarginStatus.POSITIVE:
                item_status.setForeground(QtGui.QColor("#276749")) # Deep green
                item_status.setBackground(QtGui.QColor("#C6F6D5")) # Soft green
            elif chk.status == MarginStatus.LOW:
                item_status.setForeground(QtGui.QColor("#975A16")) # Deep orange
                item_status.setBackground(QtGui.QColor("#FEEBC8")) # Soft orange
            else:
                item_status.setForeground(QtGui.QColor("#9B2C2C")) # Deep red
                item_status.setBackground(QtGui.QColor("#FED7D7")) # Soft red
                
            self.table_checks.setItem(row, 0, item_name)
            self.table_checks.setItem(row, 1, item_applied)
            self.table_checks.setItem(row, 2, item_ms)
            self.table_checks.setItem(row, 3, item_status)
