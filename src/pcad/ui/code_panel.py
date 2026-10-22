"""Code Editor and Code-to-Template Panel."""

from PySide6 import QtCore, QtGui, QtWidgets

DEFAULT_SCRIPT_TEMPLATE = '''"""Parametric build123d Script."""
import build123d as bd

# Parameters
width = 40.0
height = 25.0
thickness = 8.0
hole_dia = 12.0

with bd.BuildPart() as p:
    bd.Box(width, height, thickness)
    bd.Cylinder(radius=hole_dia/2.0, height=thickness*2, mode=bd.Mode.SUBTRACT)

result = p.part
'''

class CodePanel(QtWidgets.QWidget):
    run_code_requested = QtCore.Signal(str) # code string
    promote_requested = QtCore.Signal(str)  # code string

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        # Toolbar
        btn_bar = QtWidgets.QHBoxLayout()
        self.btn_run = QtWidgets.QPushButton("▶ Run Script (Çalıştır)", self)
        self.btn_run.setStyleSheet("font-weight: bold; background-color: #3182CE; color: white; padding: 6px;")
        self.btn_run.clicked.connect(self._on_run_clicked)
        btn_bar.addWidget(self.btn_run)
        
        self.btn_promote = QtWidgets.QPushButton("⚡ Promote to Template (Şablona Çevir)", self)
        self.btn_promote.clicked.connect(self._on_promote_clicked)
        btn_bar.addWidget(self.btn_promote)
        
        layout.addLayout(btn_bar)
        
        # Editor
        self.editor = QtWidgets.QPlainTextEdit(self)
        font = QtGui.QFont("Consolas", 10)
        font.setStyleHint(QtGui.QFont.Monospace)
        self.editor.setFont(font)
        self.editor.setPlainText(DEFAULT_SCRIPT_TEMPLATE)
        layout.addWidget(self.editor)

    def _on_run_clicked(self):
        code = self.editor.toPlainText().strip()
        if code:
            self.run_code_requested.emit(code)

    def _on_promote_clicked(self):
        code = self.editor.toPlainText().strip()
        if code:
            self.promote_requested.emit(code)

    def set_code(self, code: str):
        self.editor.setPlainText(code)
