# PCAD — Parametric CAD (Engineering Edition)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-58%20passed%20(100%25)-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-LGPLv3%2FApache--2.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

**PCAD** is a 100% offline, local, deterministic parametric CAD desktop application. It generates standard B-Rep CAD models via Python code or dynamic forms, evaluates engineering stress/margin-of-safety checks in real time, and exports **STEP (AP214), STL, PNG, and PDF Engineering Datasheets** in under five minutes.

---

## 🌟 Core Principles

1. **Deterministic & Free of LLM Hallucinations:** Geometries are generated strictly through analytical mathematics and OpenCASCADE / `build123d` B-Rep kernels. The identical set of parameters always produces bit-for-bit identical CAD models.
2. **100% Local & Air-Gapped:** Zero cloud dependencies, zero external APIs, and no account creation. Your proprietary design data never leaves your workstation.
3. **Schema-Driven (Zero-UI-Code):** The graphical user interface dynamically generates from Pydantic schemas. Adding a new CAD template requires zero PySide6/Qt code.
4. **Single Pipeline, Three Workflows:**
   - **Mode A — Template Mode:** Fill parameters in dynamic forms to produce parts and engineering margin reports in seconds.
   - **Mode B — Code Mode:** Freeform parametric script modeling using `build123d` and Python in an integrated editor with instant syntax/runtime error diagnostics.
   - **Mode C — Promote-to-Template:** Automatically parse function parameters via AST inspection and turn any Python script into a reusable, validated UI form template with one click.
5. **Crash-Proof Subprocess Architecture:** The CAD kernel runs in an isolated worker subprocess. Heavy meshing or geometry computation failures will never freeze or crash the main desktop UI.
6. **Built-in Engineering Standards Verification:** Evaluates physical properties (mass, center of gravity, 3D principal moments of inertia) and computes analytical **Margins of Safety (MS)** against recognized international standards (ISO, DIN, ASME, AGMA, and Bruhn airframe criteria).

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ (Windows 10 / 11 x64, Linux, or macOS)

### Installation
```powershell
# Clone the repository
git clone https://github.com/mesleken/parametric-cad.git
cd parametric-cad

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Linux/macOS: source .venv/bin/activate

# Install dependencies in editable mode
pip install -e .
```

### Launching the Application

#### Option 1: Desktop Shortcut / Batch Script (Windows)
Double-click `baslat.bat` in the repository root or the **Parametrik CAD** desktop shortcut.

#### Option 2: Command Line
```powershell
# Launch Desktop GUI
python -m pcad
# or
pcad gui
```

---

## 💻 Headless CLI & Automated Production

PCAD includes a full command-line interface for automated, batch, and CI/CD pipelines.

### Single Model Headless Generation
```powershell
# Generate a STEP model without opening the GUI
python -m pcad gen mech.spur_gear --params '{"module": 2.5, "num_teeth": 28, "profile_shift": 0.2}' --format step --output ./gear.step
```

### Batch Production via CSV (Automated Parametric Sweep)
Generate dozens of dimensional variations from a CSV table with a single command:
```powershell
python -m pcad batch demo.flange dimensions.csv --out-dir ./batch_outputs --material AISI4140
```

### Automated System Self-Test
Verify all built-in templates, B-Rep geometries, physics calculations, STEP round-trips, watertight STLs, and PDF datasheets:
```powershell
python -m pcad selftest
```

### Running Test Suite
```powershell
pytest tests/ -v
```

---

## 📦 Built-In Standards-Compliant Template Library

| Template ID | Category | Description & Geometry | Analytical Standards & Checks |
| :--- | :--- | :--- | :--- |
| **`aero.lug`** | Aerospace & Structural | Attachment pin lug with root transition fillet and oblique load angle ($\theta$) | **Bruhn D1.2 - D1.5 / NASA-CR-505:** Net-section tension, pin bearing, shear tear-out, and oblique interaction $(R_a^{1.6} + R_{tr}^{1.6} \le 1.0)$. |
| **`aero.clevis`** | Aerospace & Structural | Double-shear U-clevis fork fitting with cylindrical mounting shank | Pin double shear stress, lug prong bearing, and pin flexural bending moment. |
| **`aero.bracket`** | Aerospace & Structural | Stiffened angle bracket with multiple triangular gusset ribs | **Steiner Parallel Axis Theorem / Eurocode:** Composite section inertia ($I_{\text{eff}}$), root flexural bending, cantilever tip deflection ($\delta \le L/250$), and bend radius ($R_{in}/t \ge 1.5$). |
| **`aero.splice_plate`** | Aerospace & Structural | Multi-row double-shear or butt splice plate fastener array | **Bruhn D2 / Niu Ch. 7 / MIL-HDBK-5:** Net-section tensile rupture, fastener hole bearing, outer row shear with load concentration ($\eta = 1.15$), and spacing ($e/d \ge 2.0$, $p/d \ge 3.0$). |
| **`mech.stepped_shaft`** | Mechanical & Transmission | Multi-journal transmission shaft with DIN 6885 Form A keyway and DIN 509 chamfers | **DIN 743 / Peterson:** Torsional shear ($\tau = \frac{16T}{\pi d_{\min}^3}$), shoulder fillet notch factor ($K_{ts}$), keyway notch effect, and shaft twist rigidity ($\theta \le 1.0^\circ$). |
| **`mech.spur_gear`** | Mechanical & Transmission | Involute spur gear with profile shift ($x$), hub bore, and DIN 6885-1 keyway | **ISO 53 / ISO 6336 / AGMA 2001:** Root tooth bending with Dolan-Broghamer $K_f$, Hertzian contact (pitting) stress ($\sigma_H$), and undercut limit ($z_{\min} = 17(1-x)$). |
| **`mech.enclosure`** | Enclosures & Electronics | Flanged electronics chassis / enclosure box with internal screw bosses | Screw boss aspect ratio ($OD/d \ge 2.0$) and thin-wall span stiffness ($t/\text{Span} \ge 1.5\%$). |
| **`demo.flange`** | Piping & Pressure Vessels | Raised Face (RF) weld-neck pipe flange with conical transition hub | **ASME Sec VIII Div 1 App. 2 / EN 1092-1 / ASME B16.5:** Hydrostatic bolt tension, hub hoop stress ($\sigma_h$), bolt ligament clearance, and outer edge margin. |

---

## 🛠️ Add a New CAD Template in Under 5 Minutes

To add a new parametric component to the library, simply create a single Python file in the templates directory:

```python
from typing import Annotated
from pydantic import BaseModel, Field
from pcad.domain.template import template, UI
import build123d as bd

class BushingParams(BaseModel):
    outer_dia: Annotated[float, Field(gt=5.0, le=200.0), UI(label="Outer Diameter", unit="mm", step=1.0)] = 30.0
    inner_dia: Annotated[float, Field(gt=2.0, le=180.0), UI(label="Inner Diameter", unit="mm", step=1.0)] = 20.0
    length:    Annotated[float, Field(gt=2.0, le=300.0), UI(label="Length",         unit="mm", step=2.0)] = 40.0

@template(
    id="custom.bushing",
    name="Flanged Bushing",
    category="Bearings & Bushings",
    params=BushingParams,
    default_material="SS316L"
)
def build(p: BushingParams):
    with bd.BuildPart() as b:
        bd.Cylinder(radius=p.outer_dia / 2.0, height=p.length)
        bd.Cylinder(radius=p.inner_dia / 2.0, height=p.length + 2.0, mode=bd.Mode.SUBTRACT)
    return b.part
```
As soon as the file is saved, the application automatically registers it, renders the dynamic parameter form, computes physical properties, provides real-time 3D visualization, and enables STEP, STL, and PDF exports.

---

## 📄 Output Formats

- **STEP (`.step`):** Standard AP214 B-Rep solid model with deterministic header normalization. Compatible with SolidWorks, Siemens NX, CATIA, PTC Creo, Autodesk Inventor, Fusion 360, and FreeCAD.
- **STL (`.stl`):** High-precision binary mesh for 3D slicing software (Bambu Studio, PrusaSlicer, Cura, OrcaSlicer) with automated watertight topological manifold validation.
- **PNG (`.png`):** High-resolution ray-shaded presentation rendering with distinct geometry contour edges.
- **PDF Engineering Datasheet (`.pdf`):** A professional 1-page engineering summary containing 3D isometric view, input parameters table, material physical/inertial properties, and color-coded Margin of Safety status badges (`POSITIVE`, `LOW MARGIN`, `NEGATIVE`).

---

## ⚖️ Architecture & Commercial Licensing

- **Clean LGPLv3 / Permissive Foundation:**
  - GUI: Built strictly with **`PySide6-Essentials` (LGPLv3)**, completely avoiding GPL-viral Qt modules.
  - Geometry Engine: Built on **`build123d` (Apache 2.0)** and OpenCASCADE Community Edition (LGPLv2.1).
  - Visualization: **`pyvistaqt` / `pyvista` (MIT License)**.
- **Crash Isolation:** Geometry generation runs exclusively within isolated worker processes, ensuring stability and performance during batch operations and complex evaluations.
