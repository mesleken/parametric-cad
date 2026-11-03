# Takviyeli L-Braket (Gusseted Bracket)

## 1. Yöntem ve Standartlar
Bu şablon, kompozit ve metal takviyeli braketler için **Steiner Paralel Eksen Teoremi**, **Eurocode / AISC Sehim Kriterleri** ve **MIL-HDBK-17** büküm kurallarını uygular.

### B-Rep Standart Geometrisi
- Rijitliği artıran $N$ adet üçgen takviye kaburgası (gusset ribs).
- İç büküm kök radyusu ($R_{\text{in}}$).

### Mühendislik Doğrulama Formülleri
1. **Steiner Paralel Eksen Teoremi ile Kompozit Alan Eylemsizlik Momenti ($I_{\text{eff}}$):**
   - Flanş ve $N$ adet kaburga için nötr eksen $y_c$:
     $$y_c = \frac{A_f y_f + \sum A_r y_r}{A_{\text{total}}}$$
   - Efektif eylemsizlik momenti:
     $$I_{\text{eff}} = \left( I_{f0} + A_f (y_f - y_c)^2 \right) + \sum \left( I_{r0} + A_r (y_r - y_c)^2 \right)$$
   - Kök eğilme gerilmesi:
     $$\sigma_b = \frac{M \cdot c_{\max}}{I_{\text{eff}}}$$

2. **Konsol Uç Sehimi ve Rijitlik Kontrolü ($\delta \le L / 250$):**
   $$\delta_{\max} = \frac{F \cdot L^3}{3 \cdot E \cdot I_{\text{eff}}} \le \frac{L}{250}$$

3. **İç Büküm Radyusu Oranı ($R_{\text{in}} / t \ge 1.5$):**
   - Kompozit delaminasyonu ve sac kıvrılma çatlaklarını önlemek için standart oran.
