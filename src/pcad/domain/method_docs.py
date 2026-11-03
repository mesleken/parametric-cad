"""Engineering method and standards reference documentation registry."""

from pathlib import Path
from typing import Dict, Optional

DOCS_DIR = Path(__file__).parents[3] / "docs" / "engineering-method"

METHOD_SUMMARIES: Dict[str, Dict[str, str]] = {
    "spur_gear": {
        "title": "Involute Spur Gear (ISO 53 / ISO 6336 / AGMA 2001)",
        "standards": "ISO 53, ISO 6336-1..5, AGMA 2001-D04, DIN 6885-1",
        "primary_checks": "Tooth root bending with Dolan-Broghamer Kf, Hertzian flank contact/pitting stress, profile-shift undercut limit",
    },
    "stepped_shaft": {
        "title": "Stepped Transmission Shaft (DIN 743 / DIN 6885 / Peterson)",
        "standards": "DIN 743-1..4, DIN 6885-1 Form A, DIN 509, Shigley Ch. 7",
        "primary_checks": "Peak torsional shear with shoulder fillet Kts and keyway notch, torsional twist rigidity (<= 1.0 deg/m)",
    },
    "lug": {
        "title": "Aerospace Pin Lug (Bruhn D1 / NASA-CR-505)",
        "standards": "Bruhn D1.2 - D1.5, NASA-CR-505, MIL-HDBK-5J",
        "primary_checks": "Analytical Ktu tension/bearing curves, transverse shear, Bruhn oblique load interaction (Ra^1.6 + Rtr^1.6 <= 1.0)",
    },
    "flange": {
        "title": "Weld-Neck Flange (EN 1092-1 / ASME Section VIII / ASME B16.5)",
        "standards": "EN 1092-1 Type 11, ASME Section VIII Div 1 App. 2, ASME B16.5",
        "primary_checks": "ASME VIII hydrostatic bolt tensile stress, hub hoop stress, bolt ligament clearance, outer edge distance",
    },
    "bracket": {
        "title": "Gusseted L-Bracket (Steiner Parallel Axis / Roark)",
        "standards": "Steiner's Parallel Axis Theorem, Eurocode 3 / AISC Deflection (L/250), MIL-HDBK-17",
        "primary_checks": "Composite T-section bending stress with exact I_eff, cantilever tip deflection stiffness, formability bend radius",
    },
    "splice_plate": {
        "title": "Bolted Splice Plate (Bruhn D2 / Niu Airframe / MIL-HDBK-5)",
        "standards": "Bruhn D2, Niu Airframe Structural Design Ch. 7, MS33540",
        "primary_checks": "Net-section tension, fastener bearing stress, outer row shear with load concentration (eta=1.15), pitch & edge ratios",
    },
}

def get_method_markdown(template_id: str) -> Optional[str]:
    """Retrieves markdown documentation file for given template id."""
    key = template_id.split(".")[-1]
    doc_path = DOCS_DIR / f"{key}.md"
    if doc_path.exists():
        return doc_path.read_text(encoding="utf-8")
    return None
