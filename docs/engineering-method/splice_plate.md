# Cıvatalı Ekleme Plakası (Bolted Splice Plate)

## 1. Yöntem ve Standartlar
Bu şablon, **Bruhn D2**, **Niu Airframe Structural Design** ve **MIL-HDBK-5J / MS33540** standartlarına uygundur.

### B-Rep Standart Geometrisi
- Çok sıralı ve çok sütunlu simetrik bağlantı deliği matrisi.
- Çift tesirli veya tek tesirli ekleme plakası konfigürasyonu.

### Mühendislik Doğrulama Formülleri
1. **Net Kesit Çekme Kopma Gerilmesi ($\sigma_{\text{net}}$):**
   $$\sigma_{\text{net}} = \frac{F}{(W - n_{\text{row}} \cdot d) \cdot t} \le F_{tu}$$

2. **Cıvata Deliği Yataklama Gerilmesi ($\sigma_{\text{brg}}$):**
   $$\sigma_{\text{brg}} = \frac{F / N_{\text{fasteners}}}{d \cdot t} \le F_{bru}$$

3. **Cıvata Kayma Gerilmesi ve Sıra Yük Dağılımı ($\tau_{\text{bolt}}$):**
   - Çok sıralı bağlantılarda plaka diferansiyel uzaması sebebiyle dış sıra $\approx \%15$ daha fazla yük taşır ($\eta = 1.15$):
     $$P_{\text{bolt,crit}} = \eta \cdot \frac{F}{N_{\text{fasteners}}}$$
     $$\tau_{\text{bolt}} = \frac{P_{\text{bolt,crit}}}{\frac{\pi}{4} d^2} \le 0.6 \cdot F_{tu}$$

4. **Havacılık Bağlantı Aralığı Kuralları:**
   - Kenar mesafesi: $e / d \ge 2.0$ (kenar yırtılmasını önler)
   - Hatve mesafesi: $p / d \ge 3.0$ (gerilme girişimini önler)
