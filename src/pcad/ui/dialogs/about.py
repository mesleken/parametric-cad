"""About & Third-Party License Dialog."""

from PySide6 import QtCore, QtGui, QtWidgets

ABOUT_TEXT = """
<h2>PCAD — Parametric CAD (Engineering Edition)</h2>
<p><b>Version:</b> 0.1.0 | <b>Release:</b> 2026 Commercial-Ready Core</p>
<p>PCAD is a 100% offline, schema-driven parametric CAD system that combines CAD geometry with real-time physical properties and analytical engineering margins.</p>
<hr/>
<h3>Third-Party Open Source Notices</h3>
<ul>
  <li><b>build123d:</b> Apache License 2.0</li>
  <li><b>OpenCascade (OCP):</b> LGPL v2.1 with Exception</li>
  <li><b>PySide6-Essentials:</b> LGPL v3 (Dynamic Linking Compliance)</li>
  <li><b>PyVista & VTK:</b> BSD 3-Clause License</li>
  <li><b>Pydantic:</b> MIT License</li>
  <li><b>ReportLab:</b> BSD License</li>
</ul>
<p><i>Under LGPL v3 terms, all Qt/PySide6 dynamic libraries are dynamically loaded and can be replaced by end-users.</i></p>
<hr/>
<p>© 2026 PCAD Engineering Team. All rights reserved.</p>
"""

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PCAD")
        self.resize(520, 420)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        browser = QtWidgets.QTextBrowser(self)
        browser.setHtml(ABOUT_TEXT)
        browser.setOpenExternalLinks(True)
        layout.addWidget(browser)
        
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok, self)
        btn_box.accepted.connect(self.accept)
        layout.addWidget(btn_box)
