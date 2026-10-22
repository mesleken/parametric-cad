# PCAD — Parametric CAD (Engineering Edition)

**PCAD**, parçaları Python koduyla veya hazır şablon formlarıyla deterministik olarak üreten, mühendislik ön boyutlandırma hesaplarını (kütle, atalet, emniyet marjları) anında yapan ve **5 dakika içinde STEP, STL, PNG ve PDF Teknik Bilgi Kartı** çıktısı veren %100 yerel ve çevrimdışı bir parametrik CAD masaüstü uygulamasıdır.

---

## 🌟 Temel Tasarım İlkeleri

1. **Deterministik ve LLM'siz:** Geometri tamamen saf matematik ve OpenCascade / `build123d` B-Rep fonksiyonlarından gelir. Aynı parametreler her zaman aynı mikron hassasiyetinde modeli üretir.
2. **%100 Yerel ve Çevrimdışı (Air-Gapped):** İnternet, bulut API'si veya kullanıcı hesabı gerekmez; verileriniz bilgisayarınızdan asla çıkmaz.
3. **Şema-Merkezli (Zero-UI-Code):** Arayüz, şablonun Pydantic şemasından otomatik üretilir. Yeni bir şablon eklemek için arayüz (PySide6) kodu yazmanız gerekmez.
4. **Tek Üretim Hattı, Üç Mod:**
   - **Mod 1 — Şablon Modu:** Hazır formları doldurarak saniyeler içinde model ve mühendislik raporu üretimi.
   - **Mod 2 — Kod Modu:** Entegre editörde `build123d` ile serbest modelleme.
   - **Mod 3 — Şablona Çevirme Modu:** Yazılan Python betiğindeki parametreleri AST ile otomatik ayrıştırıp tek tıkla form şablonuna dönüştürme.
5. **İzole Süreç Mimarisi (Crash-Proof IPC):** CAD motoru ve geometri hesaplamaları ayrı bir alt süreçte (`Worker Process`) çalışır. Geometri hataları veya ağır hesaplamalar masaüstü arayüzünü asla dondurmaz veya çökertmez.
6. **Mühendislik Doğrulaması:** Parça sadece geometri olarak değil; kütle, ağırlık merkezi, atalet tensörü ve analitik mukavemet marjları (**Margin of Safety - MS**) ile birlikte doğrulanır.

---

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.12+ (Windows 10 / 11 x64)

### Kurulum
```powershell
# Sanal ortam oluşturma ve etkinleştirme
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Bağımlılıkları ve paketi kurma
pip install -e .
```

### Çalıştırma
```powershell
# Masaüstü Arayüzünü Başlatma
python main.py
# veya
python -m pcad gui
```

### Komut Satırından Tekil ve Toplu Model Üretimi (CLI)
```powershell
# Arayüz açmadan tekil STEP modeli üretme
python -m pcad gen mech.spur_gear --params '{"module": 2.5, "num_teeth": 30}' --format step --output ./disli.step

# CSV tablosundan onlarca ölçü varyasyonunu tek komutla toplu üretme
python -m pcad batch demo.flange olculer.csv --out-dir ./ciktilar
```

### Otomatik Sistem Öz-Testi (CLI)
Arayüzü açmadan tüm şablonların geometri inşasını, fiziksel hesaplarını, STEP toleranslarını, STL ve PDF çıktılarını doğrulamak için:
```powershell
python -m pcad selftest
```

### Birim ve Entegrasyon Testleri
```powershell
pytest tests/ -v
```

---

## 📦 Yerleşik Şablon Kütüphanesi

| Şablon ID | Kategori | Açıklama | Mühendislik Doğrulaması |
| :--- | :--- | :--- | :--- |
| **`aero.lug`** | Havacılık & Yapısal | Pimli Bağlantı Kulağı (Attachment Lug) ve montaj flanşı | Net-kesit çekme, pim yataklama, kenar yırtılması marjları (Bruhn D1), $e/D \ge 1.5$ ve $W/D \ge 2.0$ kural kontrolleri |
| **`aero.clevis`** | Havacılık & Yapısal | Çatal Bağlantı Elemanı (U-Clevis Fitting) ve silindirik şaft | Çift tesirli pim kesme gerilmesi, kulak yataklama gerilmesi, pim eğilme momenti kontrolü |
| **`aero.bracket`** | Havacılık & Yapısal | Takviye Kaburgalı L-Braket (Gusseted Angle Bracket) | Kök konsol eğilme gerilmesi, kompozit ve metal delaminasyon önleme kuralı ($R_{in}/t \ge 1.5$) |
| **`aero.splice_plate`** | Havacılık & Yapısal | Çok Sıralı Cıvatalı Ekleme Plakası (Bolted Splice Plate) | Net kesit çekme, cıvata yataklama gerilmesi, $e/d \ge 2.0$ kenar ve $p/d \ge 3.0$ hatve kuralları |
| **`mech.stepped_shaft`** | Mekanik & Güç İletimi | Kademeli Şanzıman / İletim Mili (DIN 6885 Kama Kanallı) | Burulma kayma gerilmesi ($\tau = \frac{16T}{\pi d^3}$), fatura geçiş radyusu oranı ($r/d_1 \ge 0.05$, DIN 743 / Peterson Kt) |
| **`mech.spur_gear`** | Mekanik & Güç İletimi | Standart Evolvent Düz Alın Dişlisi (Gövde ve Delikli) | Lewis diş kökü eğilme gerilmesi (AGMA 2001), alt kesilme (undercut) geometrik sınırı ($z \ge 17$) |
| **`mech.enclosure`** | Muhafaza & Kasalar | Montaj Kuleli Cihaz / Modül Kasası (Elektronik Kutusu) | Vida kulesi et payı oranı ($OD/d \ge 2.0$), cidar rijitliği oranı ($t/\text{Span} \ge 1.5\%$) |
| **`demo.flange`** | Standart & Boru | Boyunlu Boru Flanşı (Weld-Neck Flange) | Cıvata dairesi (PCD) delikler arası minimum et payı (ligament) ve dış kenar payı ($OD - PCD$) kontrolü |

---

## 🛠️ 5 Dakikada Yeni Şablon Ekleme

Yeni bir parça şablonu eklemek için tek yapmanız gereken `templates/` dizinine bir `.py` dosyası bırakmaktır:

```python
from typing import Annotated
from pydantic import BaseModel, Field
from pcad.domain.template import template, UI
import build123d as bd

class BoxParams(BaseModel):
    length: Annotated[float, Field(gt=1), UI(label="Length", unit="mm", step=5)] = 50.0
    width:  Annotated[float, Field(gt=1), UI(label="Width",  unit="mm", step=5)] = 30.0
    height: Annotated[float, Field(gt=1), UI(label="Height", unit="mm", step=5)] = 10.0

@template(
    id="custom.box",
    name="Custom Box",
    category="General",
    params=BoxParams,
    default_material="Al6061-T6"
)
def build(p: BoxParams):
    with bd.BuildPart() as b:
        bd.Box(p.length, p.width, p.height)
    return b.part
```
Bu dosya kaydedildiği anda form kontrolleri, 3B önizleme ve STEP/STL/PDF dışa aktarma yetenekleri otomatik olarak devreye girer.

---

## 📄 Çıktı Formatları

- **STEP (`.step`):** SolidWorks, Siemens NX, CATIA, Fusion 360 ve FreeCAD ile %100 uyumlu AP214 katı model (B-Rep). Deterministik başlık normalizasyonu ile aynı parametreler her zaman baytı baytına aynı dosyayı verir.
- **STL (`.stl`):** 3B baskı dilimleyicileri (Bambu Studio, PrusaSlicer, Cura) için ayarlanabilir açısal ve doğrusal yüzey toleranslı ikili (binary) mesh.
- **PNG (`.png`):** Yüksek çözünürlüklü, yumuşak gölgeli ve belirgin kenar çizgili 3B sunum görseli.
- **PDF Teknik Bilgi Kartı (`.pdf`):** Parça 3B görselini, girilen tüm parametreler tablosunu, malzeme ve fiziksel kütle/atalet özelliklerini, mühendislik emniyet marjları (MS) ve durum rozetlerini (`POSITIVE`, `LOW MARGIN`, `NEGATIVE`) içeren 1 sayfalık teknik doküman.

---

## ⚖️ Lisans ve Ticari Uyumluluk

- Uygulama, ticari satış ve kapalı kaynak dağıtıma uygun lisanslara sahiptir:
  - Arayüzde GPL-bağlayıcı modüllerden kaçınılmış, yalnızca **LGPLv3 lisanslı `PySide6-Essentials`** kullanılmıştır.
  - CAD motorunda Apache 2.0 lisanslı `build123d` ve LGPLv2.1 lisanslı OpenCascade dinamik kütüphaneleri kullanılmıştır.
