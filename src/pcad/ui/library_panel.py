"""Template Library Panel with dynamic search, category filtering, and metadata badges."""

from typing import Dict, List, Optional
from PySide6 import QtCore, QtGui, QtWidgets

from pcad.domain.i18n import t
from pcad.domain.template import TemplateSpec
from pcad.templates.registry import TemplateRegistry

class LibraryPanel(QtWidgets.QWidget):
    template_selected = QtCore.Signal(str) # template_id

    def __init__(self, registry: Optional[TemplateRegistry] = None, parent=None):
        super().__init__(parent)
        self.registry = registry or TemplateRegistry.get_default_registry()
        self._current_template_id: Optional[str] = None
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # 1. Search Box
        self.search_edit = QtWidgets.QLineEdit(self)
        self.search_edit.setPlaceholderText("🔍 " + t("library.search_placeholder", default="Şablon ara / Search..."))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_edit)
        
        # 2. Category Filter Combo
        self.combo_category = QtWidgets.QComboBox(self)
        self.combo_category.addItem("📂 Tüm Kategoriler (All Categories)", "all")
        self.combo_category.currentIndexChanged.connect(self._apply_filter)
        layout.addWidget(self.combo_category)
        
        # 3. Main Templates Tree / List
        self.tree = QtWidgets.QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(14)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        layout.addWidget(self.tree)
        
        # Populate
        self.refresh()

    def refresh(self):
        """Reloads all templates from registry and rebuilds the category tree."""
        self.registry.reload()
        templates = self.registry.list_templates()
        
        # Collect unique categories
        categories = sorted(list({tpl.category for tpl in templates}))
        current_cat_data = self.combo_category.currentData()
        
        self.combo_category.blockSignals(True)
        self.combo_category.clear()
        self.combo_category.addItem("📂 Tüm Kategoriler (All)", "all")
        for cat in categories:
            self.combo_category.addItem(f"📁 {cat}", cat)
        
        idx = self.combo_category.findData(current_cat_data)
        if idx >= 0:
            self.combo_category.setCurrentIndex(idx)
        self.combo_category.blockSignals(False)
        
        self._apply_filter()

    def _apply_filter(self):
        search_query = self.search_edit.text().strip().lower()
        selected_category = self.combo_category.currentData() or "all"
        templates = self.registry.list_templates()
        
        self.tree.blockSignals(True)
        self.tree.clear()
        
        # Group templates by category
        grouped: Dict[str, List[TemplateSpec]] = {}
        for tpl in templates:
            # Filter by category
            if selected_category != "all" and tpl.category != selected_category:
                continue
                
            # Filter by search text (ID, name, description)
            name_str = t(tpl.name).lower() if isinstance(tpl.name, dict) else str(tpl.name).lower()
            desc_str = t(tpl.description).lower() if isinstance(tpl.description, dict) else str(tpl.description).lower()
            if search_query and (search_query not in tpl.id.lower() and search_query not in name_str and search_query not in desc_str):
                continue
                
            grouped.setdefault(tpl.category, []).append(tpl)
            
        # Add to tree
        selected_item = None
        for cat_name, cat_templates in grouped.items():
            cat_item = QtWidgets.QTreeWidgetItem(self.tree, [f"{cat_name} ({len(cat_templates)})"])
            cat_item.setFont(0, QtGui.QFont("", -1, QtGui.QFont.Bold))
            cat_item.setFlags(cat_item.flags() & ~QtCore.Qt.ItemIsSelectable)
            cat_item.setExpanded(True)
            
            for tpl in cat_templates:
                name_text = t(tpl.name) if isinstance(tpl.name, dict) else str(tpl.name)
                is_user = tpl.id.startswith("user.")
                badge = "[User]" if is_user else "[Core]"
                item_label = f"{name_text} {badge}"
                
                tpl_item = QtWidgets.QTreeWidgetItem(cat_item, [item_label])
                tpl_item.setData(0, QtCore.Qt.UserRole, tpl.id)
                tpl_item.setToolTip(0, f"ID: {tpl.id} (v{tpl.version})\n{t(tpl.description)}")
                
                if self._current_template_id == tpl.id:
                    selected_item = tpl_item
                    
        self.tree.blockSignals(False)
        
        # Restore selection or select first
        if selected_item:
            self.tree.setCurrentItem(selected_item)
        elif self.tree.topLevelItemCount() > 0:
            first_cat = self.tree.topLevelItem(0)
            if first_cat.childCount() > 0:
                self.tree.setCurrentItem(first_cat.child(0))

    def _on_tree_selection_changed(self):
        items = self.tree.selectedItems()
        if not items:
            return
        tpl_id = items[0].data(0, QtCore.Qt.UserRole)
        if tpl_id and tpl_id != self._current_template_id:
            self._current_template_id = tpl_id
            self.template_selected.emit(tpl_id)

    def select_template(self, template_id: str):
        """Programmatically selects a template by ID."""
        self._current_template_id = template_id
        
        # Traverse tree items to find match
        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                if child.data(0, QtCore.Qt.UserRole) == template_id:
                    self.tree.setCurrentItem(child)
                    return

    def get_selected_template_id(self) -> Optional[str]:
        return self._current_template_id
