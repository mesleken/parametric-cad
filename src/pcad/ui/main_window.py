"""Main Window for Parametric CAD application."""

from pathlib import Path
import uuid
from typing import Optional
from PySide6 import QtCore, QtGui, QtWidgets

from pcad.domain.i18n import get_language, set_language, t
from pcad.domain.project import ProjectData, load_project, save_project
from pcad.domain.template import TemplateSpec
from pcad.runtime.client import WorkerClient
from pcad.runtime.protocol import BuildRequest, BuildResult, ExportRequest, ExportResult, WorkerError
from pcad.templates.registry import TemplateRegistry
from pcad.ui.code_panel import CodePanel
from pcad.ui.form_builder import SchemaFormWidget
from pcad.ui.library_panel import LibraryPanel
from pcad.ui.results_panel import ResultsPanel
from pcad.ui.viewport import CadViewport

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCAD - Parametric CAD (Engineering Edition)")
        self.resize(1380, 860)
        
        self.registry = TemplateRegistry.get_default_registry()
        self.current_template: Optional[TemplateSpec] = None
        self.current_model_hash: str = ""
        
        # Worker Client
        self.client = WorkerClient(self)
        self.client.build_started.connect(self._on_build_started)
        self.client.build_finished.connect(self._on_build_finished)
        self.client.build_failed.connect(self._on_build_failed)
        self.client.export_finished.connect(self._on_export_finished)
        self.client.export_failed.connect(self._on_export_failed)
        
        self._init_ui()
        self._setup_toolbar()
        
        # Load default template
        self._load_initial_template()

    def _init_ui(self):
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)
        
        # Splitter dividing Left (Tabs: Form & Library), Center (Viewport), Right (Results & Code)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        
        # 1. Left Tab Widget: Tab 0 = Form Parameters, Tab 1 = Template Library Tree
        self.left_tabs = QtWidgets.QTabWidget(self)
        
        # Tab 0: Parameters & Schema Form
        form_tab = QtWidgets.QWidget()
        form_tab_layout = QtWidgets.QVBoxLayout(form_tab)
        form_tab_layout.setContentsMargins(4, 4, 4, 4)
        form_tab_layout.setSpacing(8)
        
        tpl_group = QtWidgets.QGroupBox(t("panel.templates"), form_tab)
        tpl_layout = QtWidgets.QVBoxLayout(tpl_group)
        tpl_layout.setSpacing(6)
        
        self.search_templates_edit = QtWidgets.QLineEdit(tpl_group)
        self.search_templates_edit.setPlaceholderText("🔍 " + t("library.search_placeholder", default="Şablon ara / Search..."))
        self.search_templates_edit.setClearButtonEnabled(True)
        self.search_templates_edit.textChanged.connect(self._on_search_templates_changed)
        tpl_layout.addWidget(self.search_templates_edit)
        
        self.combo_templates = QtWidgets.QComboBox(tpl_group)
        self._repopulate_templates()
        self.combo_templates.currentIndexChanged.connect(self._on_template_selected)
        tpl_layout.addWidget(self.combo_templates)
        form_tab_layout.addWidget(tpl_group)
        
        self.form_widget = SchemaFormWidget(parent=form_tab)
        self.form_widget.values_changed.connect(self._on_form_values_changed)
        form_tab_layout.addWidget(self.form_widget)
        
        self.left_tabs.addTab(form_tab, "⚙️ Parametreler")
        
        # Tab 1: Comprehensive Template Library Panel
        self.library_panel = LibraryPanel(registry=self.registry, parent=self.left_tabs)
        self.library_panel.template_selected.connect(self._on_template_selected_from_library)
        self.left_tabs.addTab(self.library_panel, "📚 Şablon Kütüphanesi")
        
        splitter.addWidget(self.left_tabs)
        
        # 2. Center Panel (3D Viewport)
        self.viewport = CadViewport(self)
        splitter.addWidget(self.viewport)
        
        # 3. Right Panel (Tabbed Results & Code Editor)
        right_tabs = QtWidgets.QTabWidget(self)
        self.results_panel = ResultsPanel(right_tabs)
        self.results_panel.material_changed.connect(self._on_material_changed)
        right_tabs.addTab(self.results_panel, t("panel.physics"))
        
        self.code_panel = CodePanel(right_tabs)
        self.code_panel.run_code_requested.connect(self._on_run_code)
        self.code_panel.promote_requested.connect(self._on_promote_code)
        right_tabs.addTab(self.code_panel, t("panel.code"))
        
        splitter.addWidget(right_tabs)
        
        # Adjust proportions: Left 340px, Center 660px, Right 380px
        splitter.setSizes([340, 660, 380])
        main_layout.addWidget(splitter)
        
        # Status Bar
        self.status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_label = QtWidgets.QLabel(t("status.ready"), self)
        self.status_bar.addWidget(self.status_label, 1)
        
        self.btn_cancel_build = QtWidgets.QPushButton("⛔ Durdur", self)
        self.btn_cancel_build.setStyleSheet("padding: 2px 8px; font-size: 11px; background: #FEB2B2; color: #742A2A; border-radius: 3px;")
        self.btn_cancel_build.setVisible(False)
        self.btn_cancel_build.clicked.connect(self._on_cancel_build)
        self.status_bar.addPermanentWidget(self.btn_cancel_build)
        
        self.hash_label = QtWidgets.QLabel("", self)
        self.hash_label.setStyleSheet("font-family: monospace; color: #4A5568;")
        self.status_bar.addPermanentWidget(self.hash_label)

    def _setup_toolbar(self):
        toolbar = QtWidgets.QToolBar("Main Toolbar", self)
        toolbar.setIconSize(QtCore.QSize(18, 18))
        self.addToolBar(toolbar)
        
        # Project File Actions
        act_open = toolbar.addAction("📂 " + t("btn.open_project"))
        act_open.triggered.connect(self._on_open_project)
        
        act_save = toolbar.addAction("💾 " + t("btn.save_project"))
        act_save.triggered.connect(self._on_save_project)
        
        toolbar.addSeparator()
        
        # Batch CSV Production
        act_batch = toolbar.addAction("⚡ Toplu Üretim (Batch CSV)")
        act_batch.setToolTip("CSV tablosundan çoklu ölçü varyasyonlarını tek tıkla üretin")
        act_batch.triggered.connect(self._show_batch_dialog)
        
        toolbar.addSeparator()
        
        # Exports
        act_step = toolbar.addAction("📦 " + t("btn.export_step"))
        act_step.triggered.connect(lambda: self._export_format("step", "STEP CAD Model (*.step)"))
        
        act_stl = toolbar.addAction("🖨 " + t("btn.export_stl"))
        act_stl.triggered.connect(lambda: self._export_format("stl", "STL 3D Print Mesh (*.stl)"))
        
        act_png = toolbar.addAction("🖼 " + t("btn.export_png"))
        act_png.triggered.connect(lambda: self._export_format("png", "PNG Image (*.png)"))
        
        act_pdf = toolbar.addAction("📄 " + t("btn.export_pdf"))
        act_pdf.triggered.connect(lambda: self._export_format("pdf", "PDF Datasheet (*.pdf)"))
        
        toolbar.addSeparator()
        
        # Diagnostics and About
        act_diag = toolbar.addAction("🩺 Diagnostics")
        act_diag.triggered.connect(self._show_diagnostics)
        
        act_about = toolbar.addAction("ℹ About")
        act_about.triggered.connect(self._show_about)
        
        # Language Switcher
        toolbar.addSeparator()
        lbl_lang = QtWidgets.QLabel("🌐 ", toolbar)
        toolbar.addWidget(lbl_lang)
        self.combo_lang = QtWidgets.QComboBox(toolbar)
        self.combo_lang.addItem("Türkçe", "tr")
        self.combo_lang.addItem("English", "en")
        current_lang = get_language()
        idx = self.combo_lang.findData(current_lang)
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)
        toolbar.addWidget(self.combo_lang)

    def _load_initial_template(self):
        templates = self.registry.list_templates()
        if templates:
            self._select_template_by_id(templates[0].id)

    def _select_template_by_id(self, template_id: str):
        idx = self.combo_templates.findData(template_id)
        if idx >= 0:
            self.combo_templates.setCurrentIndex(idx)
        else:
            self.current_template = self.registry.get(template_id)
            self._on_template_selected(-1)

    def _on_template_selected_from_library(self, template_id: str):
        """Called when a template is clicked in the Library tree; selects it and flips to Form tab."""
        idx = self.combo_templates.findData(template_id)
        if idx >= 0:
            self.combo_templates.setCurrentIndex(idx)
        self.left_tabs.setCurrentIndex(0)

    def _repopulate_templates(self, select_id: Optional[str] = None):
        self.combo_templates.blockSignals(True)
        self.combo_templates.clear()
        
        search_text = self.search_templates_edit.text().strip().lower() if hasattr(self, "search_templates_edit") else ""
        templates = self.registry.list_templates()
        
        for tpl in templates:
            name_str = t(tpl.name) if isinstance(tpl.name, dict) else str(tpl.name)
            desc_str = t(tpl.description) if isinstance(tpl.description, dict) else str(tpl.description)
            if search_text and (search_text not in tpl.id.lower() and search_text not in name_str.lower() and search_text not in desc_str.lower()):
                continue
            is_user = tpl.id.startswith("user.")
            badge = "[Kullanıcı]" if is_user else f"[{tpl.category}]"
            display_text = f"{badge} {name_str} (v{tpl.version})"
            self.combo_templates.addItem(display_text, tpl.id)
            
        if select_id:
            idx = self.combo_templates.findData(select_id)
            if idx >= 0:
                self.combo_templates.setCurrentIndex(idx)
        self.combo_templates.blockSignals(False)

    def _on_search_templates_changed(self, text: str):
        cur_data = self.combo_templates.currentData()
        self._repopulate_templates(select_id=cur_data)

    def _on_template_selected(self, index: int):
        template_id = self.combo_templates.itemData(index) if index >= 0 else (self.current_template.id if self.current_template else None)
        if not template_id:
            return
        self.current_template = self.registry.get(template_id)
        
        # Cancel any pending debounced build from previous template
        self.client.cancel_pending()
        
        # Block signals during template switch
        self.results_panel.blockSignals(True)
        self.results_panel.set_material_id(self.current_template.default_material)
        self.results_panel.blockSignals(False)
        
        # Build form for new template with AST constraints
        self.form_widget.blockSignals(True)
        self.form_widget.build_form(self.current_template.param_cls, template_spec=self.current_template)
        self.form_widget.blockSignals(False)
        
        # Load method doc if available
        doc_name = template_id.split(".")[-1]
        doc_path = Path(__file__).parents[3] / "docs" / "engineering-method" / f"{doc_name}.md"
        if doc_path.exists():
            self.results_panel.set_method_doc(template_id, doc_path.read_text(encoding="utf-8"))
        else:
            desc = t(self.current_template.description) if self.current_template.description else "Standard parametric CAD template."
            self.results_panel.set_method_doc(
                template_id,
                f"# {t(self.current_template.name)}\n\n{desc}\n\n*Reference: See docs/REFERENCES.md*"
            )
            
        # Trigger immediate build for newly selected template
        self._trigger_current_build(immediate=True)

    def _on_form_values_changed(self, values: dict):
        self._trigger_current_build(immediate=False)

    def _on_material_changed(self, material_id: str):
        self._trigger_current_build(immediate=False)

    def _trigger_current_build(self, immediate: bool = False):
        if not self.current_template:
            return
        params = self.form_widget.get_values()
        material_id = self.results_panel.get_selected_material_id()
        req = BuildRequest(
            req_id=str(uuid.uuid4())[:8],
            source="template",
            template_id=self.current_template.id,
            template_version=self.current_template.version,
            params=params,
            material_id=material_id
        )
        if immediate:
            self.client.request_build_immediate(req)
        else:
            self.client.request_build_debounced(req)

    def _on_run_code(self, code: str):
        material_id = self.results_panel.get_selected_material_id()
        req = BuildRequest(
            req_id=str(uuid.uuid4())[:8],
            source="code",
            code=code,
            material_id=material_id
        )
        self.client.request_build_immediate(req)

    def _on_promote_code(self, code: str):
        from pcad.ui.dialogs.save_wizard import SaveTemplateWizardDialog
        dlg = SaveTemplateWizardDialog(code, self)
        if dlg.exec() == QtWidgets.QDialog.Accepted and dlg.created_template_id:
            tpl_id = dlg.created_template_id
            self.registry.reload()
            self._repopulate_templates(select_id=tpl_id)
            self.library_panel.refresh()
            idx = self.combo_templates.findData(tpl_id)
            if idx >= 0:
                self.combo_templates.setCurrentIndex(idx)
                self._on_template_selected(idx)
            QtWidgets.QMessageBox.information(
                self,
                "Şablon Eklendi",
                f"Kod başarıyla parametrik şablona dönüştürüldü ve kütüphaneye eklendi!\nID: {tpl_id}\nKonum:\n{dlg.saved_path}"
            )

    def _on_cancel_build(self):
        self.client.cancel_current()
        self.status_label.setText("Üretim durduruldu. (Mevcut model korundu)")
        self.btn_cancel_build.setVisible(False)

    def _on_build_started(self, req_id: str):
        self.status_label.setText(t("status.generating"))
        self.btn_cancel_build.setVisible(True)

    def _on_build_finished(self, result: BuildResult):
        self.btn_cancel_build.setVisible(False)
        self.current_model_hash = result.model_hash
        total_time = result.timings_ms.get("total", 0.0)
        
        # Clear code error if any
        self.code_panel.clear_error()
        
        # Display status message including any post-generation warnings
        if result.warnings:
            warn_msg = " | ".join(result.warnings)
            self.status_label.setText(f"⚠️ {warn_msg} (Süre: {total_time:.0f} ms)")
        else:
            self.status_label.setText(t("status.done", time_ms=total_time))
            
        self.hash_label.setText(f"Hash: {result.model_hash[:10]}")
        
        # Update 3D viewport
        self.viewport.load_mesh_from_npz(result.mesh_path)
        
        # Update results panel
        self.results_panel.update_physics(result.physics)
        self.results_panel.update_checks(result.checks)

    def _on_build_failed(self, error: WorkerError):
        self.btn_cancel_build.setVisible(False)
        msg = error.message_key
        self.status_label.setText(f"❌ {msg}")
        
        # In code mode, display detailed line error and snippet in code editor
        if error.kind == "code_error":
            self.code_panel.set_error(error.message_key, error.line_no, error.hint)

    def _export_format(self, fmt: str, filter_str: str):
        if not self.current_model_hash:
            QtWidgets.QMessageBox.warning(self, "Export", "Please generate a valid model before exporting.")
            return
            
        default_name = f"{self.current_template.id if self.current_template else 'model'}_{self.current_model_hash[:8]}.{fmt}"
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, f"Export {fmt.upper()}", default_name, filter_str)
        if not file_path:
            return
            
        req = ExportRequest(
            req_id=str(uuid.uuid4())[:8],
            model_hash=self.current_model_hash,
            export_format=fmt,
            output_path=file_path
        )
        self.status_label.setText(f"Exporting {fmt.upper()} to {Path(file_path).name}...")
        self.client.request_export(req)

    def _on_export_finished(self, result: ExportResult):
        self.status_label.setText(f"✓ Export completed: {Path(result.output_path).name}")
        QtWidgets.QMessageBox.information(
            self,
            "Export Successful",
            f"File successfully exported to:\n{result.output_path}"
        )

    def _on_export_failed(self, error_msg: str):
        self.status_label.setText(f"Export error: {error_msg}")
        QtWidgets.QMessageBox.critical(self, "Export Failed", f"Export operation failed:\n{error_msg}")

    def _on_save_project(self):
        if not self.current_template:
            return
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Project", f"{self.current_template.id}.pcad.json", "PCAD Project (*.pcad.json)"
        )
        if not file_path:
            return
            
        data = ProjectData(
            template_id=self.current_template.id,
            template_version=self.current_template.version,
            params=self.form_widget.get_values(),
            material_id=self.results_panel.get_selected_material_id()
        )
        save_project(data, file_path)
        self.status_label.setText(f"Project saved to {Path(file_path).name}")

    def _on_open_project(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Project", "", "PCAD Project (*.pcad.json)"
        )
        if not file_path:
            return
            
        try:
            data = load_project(file_path)
            self._select_template_by_id(data.template_id)
            self.results_panel.set_material_id(data.material_id)
            self.form_widget.set_values(data.params)
            self.status_label.setText(f"Loaded project {Path(file_path).name}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load project:\n{e}")

    def _show_batch_dialog(self):
        from pcad.ui.dialogs.batch_dialog import BatchProductionDialog
        current_tpl_id = self.current_template.id if self.current_template else "demo.flange"
        dlg = BatchProductionDialog(default_template_id=current_tpl_id, parent=self)
        dlg.exec()

    def _show_diagnostics(self):
        from pcad.ui.dialogs.diagnostics_dialog import DiagnosticsDialog
        dlg = DiagnosticsDialog(self)
        dlg.exec()

    def _show_about(self):
        QtWidgets.QMessageBox.about(
            self,
            "About PCAD",
            "<b>PCAD - Parametric CAD Application</b><br>"
            "Engineering Edition v0.2.0<br><br>"
            "Offline-first, schema-driven parametric 3D CAD modeling system.<br>"
            "Deterministic solid geometry backed by OpenCASCADE and build123d.<br><br>"
            "© 2026 Meslek CAD Systems."
        )

    def _on_language_changed(self, index: int):
        lang = self.combo_lang.itemData(index)
        set_language(lang)
        self._repopulate_templates(select_id=self.current_template.id if self.current_template else None)
        if self.current_template:
            self._on_template_selected(-1)
        self.library_panel.refresh()

    def closeEvent(self, event):
        self.client.close()
        super().closeEvent(event)
