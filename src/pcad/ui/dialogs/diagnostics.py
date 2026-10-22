"""Diagnostics and Offline Support Package Exporter."""

import json
import os
import platform
import sys
import zipfile
from pathlib import Path
from PySide6 import QtWidgets
import platformdirs

class DiagnosticsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Diagnostics & Support")
        self.resize(540, 420)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        info_group = QtWidgets.QGroupBox("Environment & Versions", self)
        form = QtWidgets.QFormLayout(info_group)
        
        self.lbl_os = QtWidgets.QLabel(f"{platform.system()} {platform.release()} ({platform.architecture()[0]})")
        self.lbl_py = QtWidgets.QLabel(sys.version.split()[0])
        self.lbl_qt = QtWidgets.QLabel("PySide6-Essentials 6.12.0")
        self.lbl_cad = QtWidgets.QLabel("build123d 0.13.0 (OCP 8.0.1)")
        self.lbl_appdata = QtWidgets.QLabel(str(platformdirs.user_data_dir("pcad", "pcad")))
        
        form.addRow("Operating System:", self.lbl_os)
        form.addRow("Python Version:", self.lbl_py)
        form.addRow("Qt Framework:", self.lbl_qt)
        form.addRow("CAD Kernel:", self.lbl_cad)
        form.addRow("Storage Path:", self.lbl_appdata)
        layout.addWidget(info_group)
        
        btn_zip = QtWidgets.QPushButton("📦 Export Offline Diagnostics Package (.zip)", self)
        btn_zip.setStyleSheet("padding: 8px; font-weight: bold;")
        btn_zip.clicked.connect(self._export_diag_zip)
        layout.addWidget(btn_zip)
        
        layout.addStretch()
        
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close, self)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _export_diag_zip(self):
        dest_file, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Diagnostics Package",
            "pcad_diagnostics.zip",
            "ZIP Archive (*.zip)"
        )
        if not dest_file:
            return
            
        diag_info = {
            "os": platform.platform(),
            "python": sys.version,
            "executable": sys.executable,
            "environment_vars": {k: v for k, v in os.environ.items() if "SECRET" not in k.upper() and "KEY" not in k.upper()}
        }
        
        try:
            with zipfile.ZipFile(dest_file, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("system_diagnostics.json", json.dumps(diag_info, indent=2))
                
                # Bundle log files if present
                log_dir = Path(platformdirs.user_log_dir("pcad", "pcad"))
                if log_dir.exists():
                    for log_f in log_dir.glob("*.log"):
                        zf.write(log_f, arcname=f"logs/{log_f.name}")
                        
            QtWidgets.QMessageBox.information(
                self,
                "Package Created",
                f"Diagnostics package successfully created at:\n{dest_file}"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Failed", str(e))
