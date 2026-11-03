# Kaynak Boyunlu Boru Flanşı (Weld-Neck Flange)

## 1. Yöntem ve Standartlar
Bu şablon, **EN 1092-1 Tip 11**, **ASME B16.5** ve **ASME Section VIII Div 1 Ek 2** standartlarına uygundur.

### B-Rep Standart Geometrisi
- **Conta Kademesi (Raised Face - RF):** EN 1092-1 / ASME B16.5 standardı $2.0$ mm conta basma yüzeyi.
- **Konik Kaynak Boynu (Tapered Hub):** Boru ile flanş diski arasında gerilme geçişini sağlayan konik boyun yapısı.

### Mühendislik Doğrulama Formülleri
1. **ASME Section VIII Ek 2 Hidrostatik Cıvata Çekme Gerilmesi:**
   - Hidrostatik son kuvvet:
     $$H = \frac{\pi}{4} \cdot G^2 \cdot P$$
     ($G$: Efektif conta çapı $\approx \frac{\text{PCD} + d_i}{2}$, $P$: Tasarım basıncı)
   - Cıvata çekme gerilmesi:
     $$\sigma_{\text{bolt}} = \frac{H}{N \cdot A_{\text{bolt,root}}} \le \sigma_{\text{allow,bolt}}$$

2. **Boyun Çevresel Halka Gerilmesi (Hub Hoop Stress):**
   $$\sigma_h = \frac{P \cdot d_i}{2 \cdot t_{\text{neck}}} \le S_m = \frac{2}{3} \sigma_y$$

3. **Cıvatalar Arası Et Kalınlığı (Ligament) ve Dış Kenar Mesafesi:**
   - $L \ge d_h$ (anahtar boşluğu kuralı)
   - $e \ge 1.25 \cdot d_h$ (kenar yırtılma kuralı)
