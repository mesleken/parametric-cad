"""Lightweight internationalization (i18n) module supporting EN and TR."""

from typing import Any, Dict, Union

# Global current language
_CURRENT_LANG = "en"

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "app.title": "Parametric CAD - Engineering Edition",
        "menu.file": "File",
        "menu.export": "Export",
        "menu.help": "Help",
        "btn.generate": "Generate Model",
        "btn.export_step": "Export STEP",
        "btn.export_stl": "Export STL",
        "btn.export_png": "Export PNG",
        "btn.export_pdf": "Export Datasheet",
        "btn.save_project": "Save Project (.pcad)",
        "btn.open_project": "Open Project (.pcad)",
        "panel.templates": "Templates",
        "panel.parameters": "Parameters",
        "panel.physics": "Physical Properties",
        "panel.engineering": "Engineering Margins",
        "panel.materials": "Material",
        "panel.code": "Code Editor",
        "status.ready": "Ready",
        "status.generating": "Generating geometry...",
        "status.done": "Done in {time_ms:.1f} ms",
        "status.error": "Error: {error}",
        "group.geometry": "Geometry",
        "group.loads": "Design Loads",
        "group.advanced": "Advanced / Factors",
        "disclaimer.engineering": "PRELIMINARY SIZING ONLY - NOT A CERTIFICATION RECORD. Independent verification required.",
        "margin.positive": "POSITIVE",
        "margin.low": "LOW MARGIN",
        "margin.negative": "NEGATIVE MARGIN",
        "unit.mm": "mm",
        "unit.n": "N",
        "unit.mpa": "MPa",
        "unit.deg": "deg",
        "err.pin_ge_width": "Pin diameter (D) must be less than lug width (W)",
        "err.edge_too_small": "Edge distance (e) must be greater than D/2",
        "err.invalid_geometry": "Geometry self-intersection or non-manifold solid generated",
    },
    "tr": {
        "app.title": "Parametrik CAD - Mühendislik Sürümü",
        "menu.file": "Dosya",
        "menu.export": "Dışa Aktar",
        "menu.help": "Yardım",
        "btn.generate": "Modeli Üret",
        "btn.export_step": "STEP Dışa Aktar",
        "btn.export_stl": "STL Dışa Aktar",
        "btn.export_png": "PNG Dışa Aktar",
        "btn.export_pdf": "Teknik Kart (PDF)",
        "btn.save_project": "Projeyi Kaydet (.pcad)",
        "btn.open_project": "Proje Aç (.pcad)",
        "panel.templates": "Şablonlar",
        "panel.parameters": "Ölçüler ve Parametreler",
        "panel.physics": "Fiziksel Özellikler",
        "panel.engineering": "Mühendislik Marjları",
        "panel.materials": "Malzeme",
        "panel.code": "Kod Editörü",
        "status.ready": "Hazır",
        "status.generating": "Geometri üretiliyor...",
        "status.done": "{time_ms:.1f} ms içinde tamamlandı",
        "status.error": "Hata: {error}",
        "group.geometry": "Genel Ölçüler",
        "group.loads": "Tasarım Yükleri",
        "group.advanced": "Gelişmiş / Faktörler",
        "disclaimer.engineering": "YALNIZCA ÖN BOYUTLANDIRMA - SERTİFİKASYON VEYA ONAY DEĞİLDİR. Bağımsız doğrulama zorunludur.",
        "margin.positive": "POZİTİF MARJ",
        "margin.low": "DÜŞÜK MARJ",
        "margin.negative": "NEGATİF MARJ",
        "unit.mm": "mm",
        "unit.n": "N",
        "unit.mpa": "MPa",
        "unit.deg": "derece",
        "err.pin_ge_width": "Pim çapı (D) kulak genişliğinden (W) küçük olmalıdır",
        "err.edge_too_small": "Kenar mesafesi (e) D/2 değerinden büyük olmalıdır",
        "err.invalid_geometry": "Geometri kesişimi veya geçersiz katı gövde oluştu",
    }
}

def set_language(lang: str) -> None:
    global _CURRENT_LANG
    if lang in TRANSLATIONS:
        _CURRENT_LANG = lang

def get_language() -> str:
    return _CURRENT_LANG

def t(key_or_dict: Union[str, Dict[str, str]], lang: str = None, **kwargs: Any) -> str:
    target_lang = lang or _CURRENT_LANG
    if isinstance(key_or_dict, dict):
        text = key_or_dict.get(target_lang) or key_or_dict.get("en") or next(iter(key_or_dict.values()), "")
    else:
        lang_dict = TRANSLATIONS.get(target_lang, TRANSLATIONS["en"])
        text = lang_dict.get(key_or_dict) or TRANSLATIONS["en"].get(key_or_dict, key_or_dict)
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
