"""Batch Production Dialog for multi-row CSV parametric generation."""

import os
import subprocess
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets

from pcad.domain.i18n import t
from pcad.services.batch_service import BatchRowResult, BatchService, BatchSummary

class BatchRunnerThread(QtCore.QThread):
    progress_signal = QtCore.Signal(int, int, object) # current, total, BatchRowResult
    finished_signal = QtCore.Signal(object)           # BatchSummary
    error_signal = QtCore.Signal(str)

    def __init__(self, template_id: str, csv_path: Path, out_dir: Path, mat_id: str, export_step: bool, export_stl: bool):
        super().__init__()
        self.template_id = template_id
        self.csv_path = csv_path
        self.out_dir = out_dir
        self.mat_id = mat_id
        self.export_step = export_step
        self.export_stl = export_stl
        self._is_cancelled = False
        self.service = BatchService()

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            summary = self.service.run_batch(
                template_id=self.template_id,
                csv_path=self.csv_path,
                output_dir=self.out_dir,
                material_id=self.mat_id,
                export_step=self.export_step,
                export_stl=self.export_stl,
                progress_callback=lambda cur, tot, res: self.progress_signal.emit(cur, tot, res),
                cancel_check=lambda: self._is_cancelled
            )
            self.finished_signal.emit(summary)
        except Exception as e:
            self.error_signal.emit(str(e))

class BatchProductionDialog(QtWidgets.QDialog):
    def __init__(self, template_id: str, template_name: str, material_id: str, parent=None):
        super().__init__(parent)
        self.template_id = template_id
        self.template_name = template_name
        self.material_id = material_id
        self.service = BatchService()
        self.runner_thread = None
        
        self.setWindowTitle("Toplu Üretim (Batch CSV Production)")
        self.resize(760, 560)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 1. Header Banner
        banner = QtWidgets.QFrame(self)
        banner.setStyleSheet("background: #EDF2F7; border-radius: 6px; padding: 8px;")
        banner_layout = QtWidgets.QHBoxLayout(banner)
        lbl_info = QtWidgets.QLabel(f"<b>Aktif Şablon:</b> {template_name} (<code>{template_id}</code>)<br/><b>Malzeme:</b> {material_id}")
        banner_layout.addWidget(lbl_info)
        
        btn_sample = QtWidgets.QPushButton("📥 Örnek CSV Şablonu İndir")
        btn_sample.clicked.connect(self._on_download_sample)
        banner_layout.addWidget(btn_sample, 0, QtCore.Qt.AlignRight)
        layout.addWidget(banner)
        
        # 2. File Selection Controls
        file_box = QtWidgets.QGroupBox("1. CSV ve Çıktı Klasörü")
        file_layout = QtWidgets.QGridLayout(file_box)
        
        file_layout.addWidget(QtWidgets.QLabel("Giriş CSV Dosyası:"), 0, 0)
        self.txt_csv = QtWidgets.QLineEdit()
        self.txt_csv.setReadOnly(True)
        file_layout.addWidget(self.txt_csv, 0, 1)
        btn_browse_csv = QtWidgets.QPushButton("Gözat...")
        btn_browse_csv.clicked.connect(self._on_browse_csv)
        file_layout.addWidget(btn_browse_csv, 0, 2)
        
        file_layout.addWidget(QtWidgets.QLabel("Çıktı Klasörü:"), 1, 0)
        default_out = str(Path.home() / "Desktop" / f"pcad_batch_{template_id.replace('.', '_')}")
        self.txt_out = QtWidgets.QLineEdit(default_out)
        file_layout.addWidget(self.txt_out, 1, 1)
        btn_browse_out = QtWidgets.QPushButton("Klasör Seç...")
        btn_browse_out.clicked.connect(self._on_browse_out)
        file_layout.addWidget(btn_browse_out, 1, 2)
        
        # Checkboxes
        opt_layout = QtWidgets.QHBoxLayout()
        self.chk_step = QtWidgets.QCheckBox("STEP CAD (.step)")
        self.chk_step.setChecked(True)
        self.chk_stl = QtWidgets.QCheckBox("STL 3D Baskı Mesh (.stl)")
        self.chk_stl.setChecked(True)
        opt_layout.addWidget(QtWidgets.QLabel("Çıktı Biçimleri:"))
        opt_layout.addWidget(self.chk_step)
        opt_layout.addWidget(self.chk_stl)
        opt_layout.addStretch()
        file_layout.addLayout(opt_layout, 2, 0, 1, 3)
        layout.addWidget(file_box)
        
        # 3. Live Progress & Status Table
        table_box = QtWidgets.QGroupBox("2. Üretim Durumu ve Raporu")
        table_layout = QtWidgets.QVBoxLayout(table_box)
        
        self.table_results = QtWidgets.QTableWidget(0, 6)
        self.table_results.setHorizontalHeaderLabels(["Satır", "Durum", "Kütle (g)", "Hacim (mm³)", "Süre (ms)", "Ayrıntı"])
        self.table_results.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table_results.verticalHeader().setVisible(False)
        self.table_results.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table_layout.addWidget(self.table_results)
        
        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        table_layout.addWidget(self.progress_bar)
        
        self.lbl_status = QtWidgets.QLabel("CSV seçilip 'Üretimi Başlat' butonuna basılması bekleniyor.")
        table_layout.addWidget(self.lbl_status)
        layout.addWidget(table_box)
        
        # 4. Action Buttons
        btn_bar = QtWidgets.QHBoxLayout()
        self.btn_open_folder = QtWidgets.QPushButton("📂 Çıktı Klasörünü Aç")
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self._on_open_output_folder)
        btn_bar.addWidget(self.btn_open_folder)
        
        btn_bar.addStretch()
        
        self.btn_cancel = QtWidgets.QPushButton("Durdur / İptal")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_bar.addWidget(self.btn_cancel)
        
        self.btn_start = QtWidgets.QPushButton("🚀 Üretimi Başlat")
        self.btn_start.setStyleSheet("font-weight: bold; background: #3182CE; color: white; padding: 6px 14px;")
        self.btn_start.clicked.connect(self._on_start)
        btn_bar.addWidget(self.btn_start)
        
        layout.addLayout(btn_bar)

    def _on_download_sample(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Örnek CSV İndir",
            f"{self.template_id}_sample.csv",
            "CSV Dosyaları (*.csv)"
        )
        if file_path:
            out_p = self.service.generate_sample_csv(self.template_id, Path(file_path))
            QtWidgets.QMessageBox.information(
                self,
                "CSV Oluşturuldu",
                f"Şablona uygun örnek CSV başarıyla kaydedildi:\n{out_p}\n\nBu dosyayı Excel ile açıp istediğiniz kadar ölçü satırı ekleyebilirsiniz."
            )
            self.txt_csv.setText(str(out_p))

    def _on_browse_csv(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "CSV Seç",
            "",
            "CSV Dosyaları (*.csv)"
        )
        if file_path:
            self.txt_csv.setText(file_path)

    def _on_browse_out(self):
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Çıktı Klasörü Seç")
        if dir_path:
            self.txt_out.setText(dir_path)

    def _on_start(self):
        csv_path = Path(self.txt_csv.text().strip())
        if not csv_path.exists() or not csv_path.is_file():
            QtWidgets.QMessageBox.warning(self, "Hata", "Lütfen geçerli bir CSV dosyası seçin.")
            return
            
        out_dir = Path(self.txt_out.text().strip())
        self.table_results.setRowCount(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_open_folder.setEnabled(False)
        self.lbl_status.setText("Toplu üretim yürütülüyor...")
        
        self.runner_thread = BatchRunnerThread(
            template_id=self.template_id,
            csv_path=csv_path,
            out_dir=out_dir,
            mat_id=self.material_id,
            export_step=self.chk_step.isChecked(),
            export_stl=self.chk_stl.isChecked()
        )
        self.runner_thread.progress_signal.connect(self._on_row_progress)
        self.runner_thread.finished_signal.connect(self._on_batch_finished)
        self.runner_thread.error_signal.connect(self._on_batch_error)
        self.runner_thread.start()

    def _on_row_progress(self, current: int, total: int, row_res: BatchRowResult):
        pct = int((current / max(total, 1)) * 100)
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(f"İşleniyor: {current} / {total} parça...")
        
        row_idx = self.table_results.rowCount()
        self.table_results.insertRow(row_idx)
        
        item_row = QtWidgets.QTableWidgetItem(str(row_res.row_index))
        item_status = QtWidgets.QTableWidgetItem(row_res.status.upper())
        item_mass = QtWidgets.QTableWidgetItem(f"{row_res.mass_g:.1f}" if row_res.mass_g is not None else "-")
        item_vol = QtWidgets.QTableWidgetItem(f"{row_res.volume_mm3:.0f}" if row_res.volume_mm3 is not None else "-")
        item_dur = QtWidgets.QTableWidgetItem(f"{row_res.duration_ms:.0f} ms")
        item_detail = QtWidgets.QTableWidgetItem(row_res.error_message or "Model üretildi ✓")
        
        if row_res.status == "success":
            item_status.setForeground(QtGui.QColor("#22543D"))
            item_status.setBackground(QtGui.QColor("#C6F6D5"))
        else:
            item_status.setForeground(QtGui.QColor("#742A2A"))
            item_status.setBackground(QtGui.QColor("#FED7D7"))
            
        self.table_results.setItem(row_idx, 0, item_row)
        self.table_results.setItem(row_idx, 1, item_status)
        self.table_results.setItem(row_idx, 2, item_mass)
        self.table_results.setItem(row_idx, 3, item_vol)
        self.table_results.setItem(row_idx, 4, item_dur)
        self.table_results.setItem(row_idx, 5, item_detail)
        self.table_results.scrollToBottom()

    def _on_batch_finished(self, summary: BatchSummary):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_open_folder.setEnabled(True)
        self.lbl_status.setText(
            f"Tamamlandı! Toplam: {summary.total_rows} | Başarılı: {summary.successful_count} | Hatalı: {summary.failed_count} ({summary.total_duration_sec} sn)"
        )
        QtWidgets.QMessageBox.information(
            self,
            "Toplu Üretim Tamamlandı",
            f"Tüm modeller üretildi!\n\n• Toplam: {summary.total_rows}\n• Başarılı: {summary.successful_count}\n• Hatalı: {summary.failed_count}\n• Süre: {summary.total_duration_sec} sn\n\nRapor ve CAD dosyaları kaydedildi:\n{summary.output_directory}"
        )

    def _on_batch_error(self, err_msg: str):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.lbl_status.setText(f"Hata: {err_msg}")
        QtWidgets.QMessageBox.critical(self, "Hata", f"Toplu üretim esnasında hata oluştu:\n{err_msg}")

    def _on_cancel(self):
        if self.runner_thread and self.runner_thread.isRunning():
            self.runner_thread.cancel()
            self.lbl_status.setText("Durdurma isteği gönderildi...")

    def _on_open_output_folder(self):
        out_dir = self.txt_out.text().strip()
        if os.path.exists(out_dir):
            if os.name == "nt":
                os.startfile(out_dir)
            else:
                subprocess.Popen(["xdg-open", out_dir])
