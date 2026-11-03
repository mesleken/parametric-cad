# Kademeli İletim Mili (Stepped Transmission Shaft)

## 1. Yöntem ve Standartlar
Bu şablon, **DIN 743** (Millerin yük taşıma kapasitesi), **DIN 6885-1** (Form A paralel kamalar) ve **DIN 509** (Rulman/fatura geçişleri) standartlarına uygundur.

### B-Rep Standart Geometrisi
- **DIN 6885 Form A Kama Kanalı:** Uçları yarı dairesel (`SlotOverall`) gerçek kama yuvası.
- **DIN 509 Fatura Pahları:** Rulman montajı ve gerilme dağılımı için standart $1.0$ mm montaj pahları.

### Mühendislik Doğrulama Formülleri
1. **Tepe Burulma Kayma Gerilmesi ($\tau_{\max}$):**
   $$\tau_0 = \frac{16 \cdot T}{\pi \cdot d_{\min}^3}$$
   $$\tau_{\max} = K_{ts} \cdot \tau_0$$
   - Peterson / DIN 743 fatura çentik faktörü:
     $$K_{ts,\text{fillet}} = 1.0 + \frac{1}{\sqrt{0.5 \cdot (r/d) + 0.1 \cdot (r/d)^2 \cdot (d/D)}}$$
   - DIN 6885 Form A kama kanalı çentik faktörü $K_{ts,\text{keyway}} \approx 2.1$
   - Akma kriteri: $\tau_{\text{yield}} = 0.577 \cdot \sigma_y$ (Von Mises)

2. **Fatura Geçiş Radyusu Oranı ($r / d_{\min} \ge 0.05$):**
   - Yorulma kırılmalarını önlemek için DIN 743 tavsiyesi.

3. **Burulma Rijitliği ve Dönme Açısı Kontrolü ($\theta' \le 1.0^\circ / \text{m}$):**
   $$\theta_{\text{rad}} = \sum_{i=1}^3 \frac{T \cdot L_i}{G \cdot J_i}, \quad G = \frac{E}{2(1 + \nu)}$$
   $$\theta' = \frac{\theta_{\text{deg}}}{L_{\text{total}} / 1000} \le 1.0^\circ / \text{m}$$
