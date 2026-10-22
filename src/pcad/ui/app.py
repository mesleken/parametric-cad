"""Application runner and styling setup."""

import sys
from PySide6 import QtCore, QtGui, QtWidgets
from pcad.ui.main_window import MainWindow

def run_app():
    # Enable High DPI scaling
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Parametric CAD")
    app.setOrganizationName("PCAD")
    
    # Modern clean styling
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    return app.exec()
