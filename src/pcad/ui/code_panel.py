"""Code Editor with Python syntax highlighting, line numbers, error highlighting, and preset templates."""

import re
from typing import Optional
from PySide6 import QtCore, QtGui, QtWidgets

# Python Syntax Highlighter using QSyntaxHighlighter
class PythonSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document: QtGui.QTextDocument):
        super().__init__(document)
        self._highlighting_rules = []

        # Keyword format
        keyword_fmt = QtGui.QTextCharFormat()
        keyword_fmt.setForeground(QtGui.QColor("#005CC5")) # Blue
        keyword_fmt.setFontWeight(QtGui.QFont.Bold)
        keywords = [
            "and", "as", "assert", "async", "await", "break", "class", "continue",
            "def", "del", "elif", "else", "except", "finally", "for", "from",
            "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
            "or", "pass", "raise", "return", "try", "while", "with", "yield"
        ]
        for kw in keywords:
            pattern = QtCore.QRegularExpression(rf"\b{kw}\b")
            self._highlighting_rules.append((pattern, keyword_fmt))

        # Build123d CAD types & constants format
        cad_fmt = QtGui.QTextCharFormat()
        cad_fmt.setForeground(QtGui.QColor("#22863A")) # Green
        cad_fmt.setFontWeight(QtGui.QFont.Bold)
        cad_types = [
            "BuildPart", "BuildSketch", "BuildLine", "Box", "Cylinder", "Sphere",
            "Cone", "Torus", "Wedge", "Circle", "Rectangle", "RegularPolygon",
            "Polyline", "Spline", "fillet", "chamfer", "extrude", "revolve",
            "sweep", "loft", "Locations", "PolarLocations", "GridLocations",
            "Mode", "Axis", "Plane", "Solid", "Part", "Shape", "Compound"
        ]
        for ct in cad_types:
            pattern = QtCore.QRegularExpression(rf"\b{ct}\b")
            self._highlighting_rules.append((pattern, cad_fmt))

        # Builtins (True, False, None, range, len, print, etc.)
        builtin_fmt = QtGui.QTextCharFormat()
        builtin_fmt.setForeground(QtGui.QColor("#6F42C1")) # Purple
        builtins = ["True", "False", "None", "int", "float", "str", "bool", "list", "dict", "range", "len", "print"]
        for bi in builtins:
            pattern = QtCore.QRegularExpression(rf"\b{bi}\b")
            self._highlighting_rules.append((pattern, builtin_fmt))

        # Number format
        num_fmt = QtGui.QTextCharFormat()
        num_fmt.setForeground(QtGui.QColor("#005CC5"))
        self._highlighting_rules.append((QtCore.QRegularExpression(r"\b\d+(\.\d+)?([eE][+-]?\d+)?\b"), num_fmt))

        # String format (single line)
        string_fmt = QtGui.QTextCharFormat()
        string_fmt.setForeground(QtGui.QColor("#032F62")) # Dark blue
        self._highlighting_rules.append((QtCore.QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_fmt))
        self._highlighting_rules.append((QtCore.QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_fmt))

        # Single-line comment format
        comment_fmt = QtGui.QTextCharFormat()
        comment_fmt.setForeground(QtGui.QColor("#6A737D")) # Muted grey
        comment_fmt.setFontItalic(True)
        self._highlighting_rules.append((QtCore.QRegularExpression(r"#[^\n]*"), comment_fmt))

    def highlightBlock(self, text: str):
        for pattern, fmt in self._highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class AdvancedCodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.error_line: Optional[int] = None
        
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self._on_text_modified)
        
        self.update_line_number_area_width(0)
        
        # Configure fonts
        font = QtGui.QFont("Consolas", 10)
        font.setStyleHint(QtGui.QFont.Monospace)
        self.setFont(font)
        
        # Highlighter
        self.highlighter = PythonSyntaxHighlighter(self.document())

    def line_number_area_width(self):
        digits = 1
        m = max(1, self.blockCount())
        while m >= 10:
            m //= 10
            digits += 1
        space = 8 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            line_color = QtGui.QColor("#F0F4F8")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        if self.error_line is not None and self.error_line >= 1:
            err_selection = QtWidgets.QTextEdit.ExtraSelection()
            err_selection.format.setBackground(QtGui.QColor("#FFE3E3"))
            err_selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            cursor = QtGui.QTextCursor(self.document())
            block = self.document().findBlockByNumber(self.error_line - 1)
            if block.isValid():
                cursor.setPosition(block.position())
                err_selection.cursor = cursor
                extra_selections.append(err_selection)
                
        self.setExtraSelections(extra_selections)

    def set_error_line(self, lineno: Optional[int]):
        self.error_line = lineno
        self.highlight_current_line()
        if lineno is not None:
            block = self.document().findBlockByNumber(lineno - 1)
            if block.isValid():
                cursor = self.textCursor()
                cursor.setPosition(block.position())
                self.setTextCursor(cursor)
                self.centerCursor()

    def _on_text_modified(self):
        if self.error_line is not None:
            self.error_line = None
            self.highlight_current_line()

    def line_number_area_paint_event(self, event):
        painter = QtGui.QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QtGui.QColor("#F8F9FA"))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                num_str = str(block_number + 1)
                if self.error_line == (block_number + 1):
                    painter.fillRect(0, int(top), self.line_number_area.width(), self.fontMetrics().height(), QtGui.QColor("#E53E3E"))
                    painter.setPen(QtGui.QColor("#FFFFFF"))
                else:
                    painter.setPen(QtGui.QColor("#A0AEC0"))
                    
                painter.drawText(
                    0, int(top), self.line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    QtCore.Qt.AlignRight, num_str
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


SNIPPET_BOX = '''"""Parametric build123d Script - Box with Bore."""
import build123d as bd

# Parameters
width = 50.0
depth = 30.0
height = 12.0
hole_dia = 14.0

with bd.BuildPart() as p:
    bd.Box(width, depth, height)
    bd.Cylinder(radius=hole_dia / 2.0, height=height * 2, mode=bd.Mode.SUBTRACT)

result = p.part
'''

SNIPPET_FLANGE = '''"""Parametric build123d Script - 4-Hole Flange."""
import build123d as bd

# Parameters
outer_dia = 80.0
inner_dia = 30.0
thickness = 8.0
bolt_circle = 60.0
bolt_hole = 6.0

with bd.BuildPart() as p:
    bd.Cylinder(radius=outer_dia / 2.0, height=thickness)
    bd.Cylinder(radius=inner_dia / 2.0, height=thickness * 2, mode=bd.Mode.SUBTRACT)
    with bd.PolarLocations(radius=bolt_circle / 2.0, count=4):
        bd.Cylinder(radius=bolt_hole / 2.0, height=thickness * 2, mode=bd.Mode.SUBTRACT)

result = p.part
'''

SNIPPET_BRACKET = '''"""Parametric build123d Script - L-Bracket."""
import build123d as bd

leg_x = 45.0
leg_z = 45.0
width = 25.0
thickness = 6.0
hole_dia = 6.5

with bd.BuildPart() as p:
    with bd.BuildSketch(bd.Plane.XZ):
        with bd.BuildLine():
            l1 = bd.Line((0, 0), (leg_x, 0))
            l2 = bd.Line((leg_x, 0), (leg_x, thickness))
            l3 = bd.Line((leg_x, thickness), (thickness, thickness))
            l4 = bd.Line((thickness, thickness), (thickness, leg_z))
            l5 = bd.Line((thickness, leg_z), (0, leg_z))
            l6 = bd.Line((0, leg_z), (0, 0))
        bd.make_face()
    bd.extrude(amount=width)
    with bd.Locations((leg_x * 0.6, width / 2.0, thickness / 2.0)):
        bd.Cylinder(radius=hole_dia / 2.0, height=thickness * 2, mode=bd.Mode.SUBTRACT)

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
        
        # Snippets dropdown
        self.combo_presets = QtWidgets.QComboBox(self)
        self.combo_presets.addItem("📝 Örnek Kod Seç / Template Snippets...", None)
        self.combo_presets.addItem("📦 Delikli Kutu (Box with Hole)", SNIPPET_BOX)
        self.combo_presets.addItem("⚙️ Boru Flanşı (4-Hole Flange)", SNIPPET_FLANGE)
        self.combo_presets.addItem("📐 L-Braket (L-Bracket)", SNIPPET_BRACKET)
        self.combo_presets.currentIndexChanged.connect(self._on_preset_selected)
        btn_bar.addWidget(self.combo_presets, 1)
        
        self.btn_run = QtWidgets.QPushButton("▶ Çalıştır (Ctrl+Enter)", self)
        self.btn_run.setStyleSheet("font-weight: bold; background-color: #3182CE; color: white; padding: 5px 12px; border-radius: 4px;")
        self.btn_run.setToolTip("Scripti worker sürecinde çalıştırır ve 3D önizlemede gösterir.")
        self.btn_run.clicked.connect(self._on_run_clicked)
        btn_bar.addWidget(self.btn_run)
        
        self.btn_promote = QtWidgets.QPushButton("⚡ Şablona Çevir", self)
        self.btn_promote.setStyleSheet("padding: 5px 10px; border-radius: 4px;")
        self.btn_promote.setToolTip("Bu scripti otomatik formlu kalıcı şablona dönüştürür.")
        self.btn_promote.clicked.connect(self._on_promote_clicked)
        btn_bar.addWidget(self.btn_promote)
        
        layout.addLayout(btn_bar)
        
        # Code Editor
        self.editor = AdvancedCodeEditor(self)
        self.editor.setPlainText(SNIPPET_BOX)
        layout.addWidget(self.editor)
        
        # Error Banner
        self.error_banner = QtWidgets.QLabel(self)
        self.error_banner.setWordWrap(True)
        self.error_banner.setStyleSheet(
            "background: #FFF5F5; color: #C53030; border: 1px solid #FEB2B2; "
            "border-radius: 4px; padding: 6px; font-size: 11px; font-weight: bold;"
        )
        self.error_banner.setVisible(False)
        layout.addWidget(self.error_banner)
        
        # Shortcut Ctrl+Return
        shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self._on_run_clicked)
        shortcut_enter = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Enter"), self)
        shortcut_enter.activated.connect(self._on_run_clicked)

    def _on_preset_selected(self, index: int):
        snippet = self.combo_presets.currentData()
        if snippet:
            self.editor.setPlainText(snippet)
            self.clear_error()

    def _on_run_clicked(self):
        code = self.editor.toPlainText().strip()
        if code:
            self.clear_error()
            self.run_code_requested.emit(code)

    def _on_promote_clicked(self):
        code = self.editor.toPlainText().strip()
        if code:
            self.promote_requested.emit(code)

    def set_code(self, code: str):
        self.editor.setPlainText(code)
        self.clear_error()

    def set_error(self, message: str, line_no: Optional[int] = None, hint: Optional[str] = None):
        """Displays error message and highlights the exact error line."""
        self.editor.set_error_line(line_no)
        display_text = f"❌ {message}"
        if hint:
            display_text += f"\n💡 İpucu: {hint}"
        self.error_banner.setText(display_text)
        self.error_banner.setVisible(True)

    def clear_error(self):
        self.editor.set_error_line(None)
        self.error_banner.setVisible(False)
