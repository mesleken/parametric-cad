"""Save Template Wizard (Şablon Kaydetme Sihirbazı) for promoting code to reusable form template."""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional
import platformdirs
from PySide6 import QtCore, QtGui, QtWidgets

from pcad.codemode.ast_extract import extract_parameters_from_ast, promote_script_to_template
from pcad.domain.i18n import t

class SaveTemplateWizardDialog(QtWidgets.QDialog):
    def __init__(self, code_str: str, parent=None):
        super().__init__(parent)
        self.code_str = code_str
        self.setWindowTitle("Şablona Dönüştür (Code-to-Template Promotion Wizard)")
        self.resize(720, 580)
        
        self.created_template_id: Optional[str] = None
        self.saved_path: Optional[Path] = None
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 1. Info Banner
        banner = QtWidgets.QFrame(self)
        banner.setStyleSheet("background: #EBF8FF; border-left: 4px solid #3182CE; padding: 8px;")
        banner_layout = QtWidgets.QVBoxLayout(banner)
        lbl_h = QtWidgets.QLabel("<b>Sihirbaz: Python Fonksiyonunu Parametrik Şablona Dönüştür</b>")
        lbl_p = QtWidgets.QLabel(
            "Kodunuzdaki fonksiyon parametreleri otomatik olarak analiz edildi. "
            "Aşağıdan şablon adını, kategorisini, birimlerini ve min/max sınırlarını yapılandırabilirsiniz."
        )
        lbl_p.setWordWrap(True)
        banner_layout.addWidget(lbl_h)
        banner_layout.addWidget(lbl_p)
        layout.addWidget(banner)
        
        # 2. Template Metadata Group
        meta_box = QtWidgets.QGroupBox("1. Şablon Genel Bilgileri")
        meta_layout = QtWidgets.QGridLayout(meta_box)
        
        meta_layout.addWidget(QtWidgets.QLabel("Şablon Kimliği (ID):"), 0, 0)
        self.txt_id = QtWidgets.QLineEdit("custom_part")
        meta_layout.addWidget(self.txt_id, 0, 1)
        
        meta_layout.addWidget(QtWidgets.QLabel("Görünen Başlık:"), 0, 2)
        self.txt_name = QtWidgets.QLineEdit("Custom Parametric Part")
        meta_layout.addWidget(self.txt_name, 0, 3)
        
        meta_layout.addWidget(QtWidgets.QLabel("Kategori:"), 1, 0)
        self.combo_cat = QtWidgets.QComboBox()
        self.combo_cat.addItems([
            "User Custom",
            "Mechanical & Drives",
            "Aerospace & Structural",
            "Standard & Piping",
            "Enclosures & Housings"
        ])
        meta_layout.addWidget(self.combo_cat, 1, 1)
        
        meta_layout.addWidget(QtWidgets.QLabel("Açıklama:"), 1, 2)
        self.txt_desc = QtWidgets.QLineEdit("User-promoted parametric CAD component.")
        meta_layout.addWidget(self.txt_desc, 1, 3)
        
        layout.addWidget(meta_box)
        
        # 3. Parameters Table
        param_box = QtWidgets.QGroupBox("2. Tespit Edilen Parametreler ve Kısıtlar")
        param_layout = QtWidgets.QVBoxLayout(param_box)
        
        self.table_params = QtWidgets.QTableWidget(0, 6)
        self.table_params.setHorizontalHeaderLabels(["Parametre", "Tip", "Varsayılan", "Min", "Max", "Birim"])
        self.table_params.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        param_layout.addWidget(self.table_params)
        layout.addWidget(param_box)
        
        # 4. Verification Output Label
        self.lbl_verify = QtWidgets.QLabel("Kaydetmeden önce 'Doğrula ve Sına' butonuna basmanız önerilir.")
        self.lbl_verify.setStyleSheet("color: #4A5568; font-style: italic;")
        layout.addWidget(self.lbl_verify)
        
        # 5. Buttons
        btn_bar = QtWidgets.QHBoxLayout()
        btn_cancel = QtWidgets.QPushButton("Vazgeç")
        btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(btn_cancel)
        
        btn_bar.addStretch()
        
        self.btn_test = QtWidgets.QPushButton("🧪 Doğrula ve Sına (3-Point Test)")
        self.btn_test.clicked.connect(self._on_test_validation)
        btn_bar.addWidget(self.btn_test)
        
        self.btn_save = QtWidgets.QPushButton("💾 Kütüphaneye Kaydet")
        self.btn_save.setStyleSheet("font-weight: bold; background: #2B6CB0; color: white; padding: 6px 14px;")
        self.btn_save.clicked.connect(self._on_save_template)
        btn_bar.addWidget(self.btn_save)
        
        layout.addLayout(btn_bar)
        
        # Populate detected parameters from AST
        self._populate_detected_parameters()

    def _populate_detected_parameters(self):
        try:
            detected = extract_parameters_from_ast(self.code_str)
            self.table_params.setRowCount(len(detected))
            
            for i, p in enumerate(detected):
                item_name = QtWidgets.QTableWidgetItem(p["name"])
                item_name.setFlags(item_name.flags() & ~QtCore.Qt.ItemIsEditable)
                
                item_type = QtWidgets.QTableWidgetItem(p["type"])
                item_def = QtWidgets.QTableWidgetItem(str(p["default"]))
                
                # Guess sensible min and max limits
                def_val = p["default"]
                if isinstance(def_val, (int, float)):
                    min_val = round(def_val * 0.1, 1) if def_val > 0 else -100.0
                    max_val = round(def_val * 5.0, 1) if def_val > 0 else 100.0
                else:
                    min_val, max_val = 0, 100
                    
                item_min = QtWidgets.QTableWidgetItem(str(min_val))
                item_max = QtWidgets.QTableWidgetItem(str(max_val))
                item_unit = QtWidgets.QTableWidgetItem("mm" if isinstance(def_val, float) else "-")
                
                self.table_params.setItem(i, 0, item_name)
                self.table_params.setItem(i, 1, item_type)
                self.table_params.setItem(i, 2, item_def)
                self.table_params.setItem(i, 3, item_min)
                self.table_params.setItem(i, 4, item_max)
                self.table_params.setItem(i, 5, item_unit)
                
            if detected:
                func_name = detected[0].get("func_name", "custom_part")
                self.txt_id.setText(func_name.lower())
                self.txt_name.setText(func_name.replace("_", " ").title())
        except Exception as e:
            self.lbl_verify.setText(f"Parametre ayrıştırma uyarısı: {e}")

    def _on_test_validation(self):
        """Runs 3-point test evaluation (default, min, max) in local scope."""
        try:
            local_scope = {}
            exec(self.code_str, {}, local_scope)
            func_name = self.txt_id.text().strip()
            
            # Find candidate callable
            fn = None
            for k, v in local_scope.items():
                if callable(v) and not k.startswith("_"):
                    fn = v
                    break
                    
            if not fn:
                raise ValueError("Kod içerisinde çağrılabilir bir Python fonksiyonu bulunamadı.")
                
            # Test default values
            default_kwargs = {}
            for row in range(self.table_params.rowCount()):
                name = self.table_params.item(row, 0).text()
                val_str = self.table_params.item(row, 2).text()
                val_type = self.table_params.item(row, 1).text()
                if val_type == "int":
                    default_kwargs[name] = int(float(val_str))
                elif val_type == "float":
                    default_kwargs[name] = float(val_str)
                else:
                    default_kwargs[name] = val_str
                    
            res = fn(**default_kwargs)
            if not hasattr(res, "volume") and not hasattr(res, "wrapped"):
                raise ValueError(f"Fonksiyon bir CAD katı nesnesi (Solid) döndürmeli, '{type(res).__name__}' döndürdü.")
                
            self.lbl_verify.setStyleSheet("color: #276749; font-weight: bold;")
            self.lbl_verify.setText(f"✓ Doğrulama Başarılı! Geçerli katı üretildi (Hacim: {getattr(res, 'volume', 0.0):.1f} mm³)")
            QtWidgets.QMessageBox.information(
                self,
                "Doğrulama Başarılı",
                f"Tebrikler! Kod başarıyla derlendi ve geçerli bir katı model üretti.\n\n"
                f"Üretilen Hacim: {getattr(res, 'volume', 0.0):.1f} mm³\n"
                "Şablonu güvenle kütüphanenize kaydedebilirsiniz."
            )
            return True
        except Exception as e:
            self.lbl_verify.setStyleSheet("color: #C53030; font-weight: bold;")
            self.lbl_verify.setText(f"✗ Doğrulama Hatası: {e}")
            QtWidgets.QMessageBox.warning(self, "Doğrulama Başarısız", f"Kod sınanırken hata oluştu:\n{e}")
            return False

    def _on_save_template(self):
        tpl_id = self.txt_id.text().strip().lower()
        if not tpl_id:
            QtWidgets.QMessageBox.warning(self, "Hata", "Lütfen geçerli bir şablon kimliği girin.")
            return
            
        tpl_name = self.txt_name.text().strip()
        tpl_cat = self.combo_cat.currentText()
        tpl_desc = self.txt_desc.text().strip()
        
        try:
            saved_path = promote_script_to_template(
                code_str=self.code_str,
                template_id=tpl_id,
                template_name=tpl_name,
                category=tpl_cat,
                description=tpl_desc
            )
            self.created_template_id = f"user.{tpl_id}"
            self.saved_path = Path(saved_path)
            self.accept()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Kayıt Hatası", f"Şablon kaydedilemedi:\n{e}")
