# Engineering References & Theoretical Foundations

PCAD implements established aerospace, structural, and mechanical engineering analysis methods for preliminary sizing and geometry validation.

## 📚 Standard References

1. **Bruhn, E. F. (1973)** — *Analysis and Design of Flight Vehicle Structures*, S.R. Jacobs & Associates.
   - **Chapter D1:** Sizing and Strength Analysis of Pinned Joints and Lugs.
   - **Chapter D2:** Riveted and Bolted Connections in Airframe Structures.
2. **MMPDS-01 (FAA / DoD)** — *Metallic Materials Properties Development and Standardization*.
   - Room-temperature design allowables (A- and B-basis) for Aerospace Alloys (Al 7075-T6, Al 6061-T6, Ti-6Al-4V).
3. **Niu, Michael C. Y. (1999)** — *Airframe Structural Design*, Conmilit Press.
   - Joint design, fastener spacing ($e/D \ge 2.0, p/D \ge 3.0$), and shear lag considerations.
4. **Roark, R. J. & Young, W. C.** — *Formulas for Stress and Strain*, 7th Edition, McGraw-Hill.
   - Flexural and cantilever bending in stiffened and unstiffened angle sections.
5. **MIL-HDBK-17 (Composite Materials Handbook)** — *Polymer Matrix Composites*.
   - Minimum bend radius guidelines for composite laminates ($R_{in} / t \ge 1.5$) to prevent delamination during molding/curing.
6. **Shigley, J. E. & Mischke, C. R.** — *Standard Handbook of Machine Design*, McGraw-Hill.
   - Bolted connections, ligament thickness, and wrench clearance rules for circular flanges.

---

## ⚠️ Engineering Disclaimer
The calculations implemented in PCAD provide **preliminary sizing and rapid margin check** tools. They do not constitute formal airworthiness certification records, nor do they replace 3D Finite Element Analysis (FEA) or physical qualification testing.
