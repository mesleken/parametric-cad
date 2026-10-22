# Engineering Method: Aerospace Attachment Lug (`aero.lug`)

## 1. Overview
The attachment lug is a critical airframe component used in hinge pins, landing gear attachments, and structural fittings. The method models an axially loaded straight lug with a single hole based on **Bruhn (Chapter D1)**.

## 2. Failure Modes Evaluated

### 2.1 Net-Section Tension
Tensile rupture across the net area perpendicular to the load:
$$\sigma_{net} = \frac{F}{(W - D) \cdot t}$$
$$\text{Margin of Safety } (MS_{net}) = \frac{F_{tu} \cdot K_{tu}}{FoS \cdot \sigma_{net}} - 1.0$$
- $F$: Applied limit axial tension load (N).
- $W$: Lug width (mm).
- $D$: Pin hole diameter (mm).
- $t$: Lug thickness (mm).
- $F_{tu}$: Material ultimate tensile strength (MPa).
- $K_{tu}$: Net-section stress concentration factor (Bruhn Fig. D1.2).

### 2.2 Pin Bearing Crushing
Local plastic crushing of the contact area between the pin and lug hole:
$$\sigma_{br} = \frac{F}{D \cdot t}$$
$$MS_{br} = \frac{F_{bru}}{FoS \cdot \sigma_{br}} - 1.0$$
- $F_{bru}$: Material ultimate bearing strength (typically $1.5 \times F_{tu}$ if not specified).

### 2.3 Shear Tear-Out (Transverse Shear)
Transverse shear failure along the 40° planes extending from hole to lug tip:
$$\tau_{out} = \frac{F}{2 \cdot (e - D/2) \cdot t}$$
$$MS_{shear} = \frac{F_{su}}{FoS \cdot \tau_{out}} - 1.0$$
- $e$: Distance from hole center to lug outer tip (mm).
- $F_{su}$: Material shear strength (MPa).

### 2.4 Geometric Proportion Guidelines
- **$e / D \ge 1.5$:** Minimum edge ratio to prevent premature shear tear-out.
- **$W / D \ge 2.0$:** Ensures balanced stress flow and prevents circumferential hoop splitting.
