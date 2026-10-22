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
from pcad.ui.results_panel import ResultsPanel
from pcad.ui.viewport import CadViewport

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCAD - Parametric CAD (Engineering Edition)")
        self.resize(1360, 840)
        
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
        
        # Splitter dividing Left (Templates & Form), Center (Viewport), Right (Results & Code)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        
        # 1. Left Panel (Template Selector + Dynamic Form)
        left_widget = QtWidgets.QWidget(self)
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        # Template selector box
        tpl_group = QtWidgets.QGroupBox(t("panel.templates"), left_widget)
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
        left_layout.addWidget(tpl_group)
        
        # Dynamic Schema Form
        self.form_widget = SchemaFormWidget(parent=left_widget)
        self.form_widget.values_changed.connect(self._on_form_values_changed)
        left_layout.addWidget(self.form_widget)
        
        splitter.addWidget(left_widget)
        
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
        
        # Adjust proportions: Left 300px, Center 680px, Right 380px
        splitter.setSizes([320, 680, 360])
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
        
        toolbar.addSeparator()
        
        # Language Switcher
        combo_lang = QtWidgets.QComboBox(self)
        combo_lang.addItems(["English (EN)", "Türkçe (TR)"])
        combo_lang.setCurrentIndex(0 if get_language() == "en" else 1)
        combo_lang.currentIndexChanged.connect(self._on_language_toggled)
        toolbar.addWidget(combo_lang)

    def _show_diagnostics(self):
        from pcad.ui.dialogs.diagnostics import DiagnosticsDialog
        dlg = DiagnosticsDialog(self)
        dlg.exec()

    def _show_about(self):
        from pcad.ui.dialogs.about import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()

    def _repopulate_templates(self, select_id: Optional[str] = None):
        filter_text = getattr(self, "search_templates_edit", None)
        query = filter_text.text().strip().lower() if filter_text else ""
        
        current_data = select_id or (self.combo_templates.currentData() if self.combo_templates.count() > 0 else None)
        self.combo_templates.blockSignals(True)
        self.combo_templates.clear()
        
        for spec in self.registry.list_templates():
            name_text = t(spec.name) if isinstance(spec.name, dict) else str(spec.name)
            desc_text = t(spec.description) if isinstance(spec.description, dict) else str(spec.description)
            is_user = spec.id.startswith("user.")
            badge = "[Özel/User]" if is_user else f"[{spec.category}]"
            
            if query and (query not in spec.id.lower() and query not in name_text.lower() and query not in desc_text.lower() and query not in spec.category.lower()):
                continue
                
            self.combo_templates.addItem(f"{name_text} {badge}", spec.id)
            
        if current_data:
            idx = self.combo_templates.findData(current_data)
            if idx >= 0:
                self.combo_templates.setCurrentIndex(idx)
        if self.combo_templates.currentIndex() < 0 and self.combo_templates.count() > 0:
            self.combo_templates.setCurrentIndex(0)
        self.combo_templates.blockSignals(False)

    def _on_search_templates_changed(self, text: str):
        self._repopulate_templates()
        if self.combo_templates.count() > 0:
            self._on_template_selected(self.combo_templates.currentIndex())

    def _show_batch_dialog(self):
        if not self.current_template:
            QtWidgets.QMessageBox.warning(self, "Toplu Üretim", "Lütfen önce bir şablon seçin.")
            return
        from pcad.ui.dialogs.batch_dialog import BatchProductionDialog
        dlg = BatchProductionDialog(
            template_id=self.current_template.id,
            template_name=t(self.current_template.name) if isinstance(self.current_template.name, dict) else str(self.current_template.name),
            material_id=self.results_panel.get_selected_material_id(),
            parent=self
        )
        dlg.exec()

    def _load_initial_template(self):
        if self.combo_templates.count() > 0:
            self._on_template_selected(0)

    def _on_template_selected(self, index: int):
        template_id = self.combo_templates.itemData(index)
        if not template_id:
            return
        self.current_template = self.registry.get(template_id)
        
        # Cancel any pending debounced build from previous template
        self.client.cancel_pending()
        
        # Block signals during template switch so material change does not fire with old stale parameters
        self.results_panel.blockSignals(True)
        self.results_panel.set_material_id(self.current_template.default_material)
        self.results_panel.blockSignals(False)
        
        # Build form for new template
        self.form_widget.blockSignals(True)
        self.form_widget.build_form(self.current_template.param_cls)
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
        self.client.restart_worker()
        self.status_label.setText("Üretim durduruldu.")
        self.btn_cancel_build.setVisible(False)

    def _on_build_started(self, req_id: str):
        self.status_label.setText(t("status.generating"))
        self.btn_cancel_build.setVisible(True)

    def _on_build_finished(self, result: BuildResult):
        self.btn_cancel_build.setVisible(False)
        self.current_model_hash = result.model_hash
        total_time = result.timings_ms.get("total", 0.0)
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
        self.status_label.setText(t("status.error", error=msg))

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
        self.status_label.setText(f"Successfully exported: {Path(result.output_path).name}")
        QtWidgets.QMessageBox.information(self, "Export Complete", f"Successfully exported file:\n{result.output_path}")

    def _on_export_failed(self, err_msg: str):
        self.status_label.setText(f"Export failed: {err_msg}")
        QtWidgets.QMessageBox.critical(self, "Export Failed", f"Could not export file:\n{err_msg}")

    def _on_save_project(self):
        if not self.current_template:
            return
        default_name = f"{self.current_template.id}_project.pcad"
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Project", default_name, "PCAD Project (*.pcad)")
        if not file_path:
            return
            
        project = ProjectData(
            template_id=self.current_template.id,
            template_version=self.current_template.version,
            params=self.form_widget.get_values(),
            material_id=self.results_panel.get_selected_material_id(),
            model_hash=self.current_model_hash
        )
        try:
            save_project(project, Path(file_path))
            QtWidgets.QMessageBox.information(self, "Project Saved", f"Project saved successfully to:\n{file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save Failed", str(e))

    def _on_open_project(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Project", "", "PCAD Project (*.pcad)")
        if not file_path:
            return
        try:
            proj = load_project(Path(file_path))
            # Switch template if needed
            idx = self.combo_templates.findData(proj.template_id)
            if idx >= 0:
                self.combo_templates.setCurrentIndex(idx)
            self.results_panel.set_material_id(proj.material_id)
            self.form_widget.set_values(proj.params)
            QtWidgets.QMessageBox.information(self, "Project Loaded", f"Project loaded from:\n{file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Load Failed", str(e))

    def _on_language_toggled(self, index: int):
        new_lang = "en" if index == 0 else "tr"
        set_language(new_lang)
        QtWidgets.QMessageBox.information(
            self,
            "Language Changed",
            "Language preference updated. Restart application to refresh all dialog labels."
        )

    def closeEvent(self, event):
        self.client.close()
        self.viewport.close()
        event.accept()
