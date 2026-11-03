# Havacılık Bağlantı Kulağı (Aerospace Pin Lug)

## 1. Yöntem ve Standartlar
Bu şablon, **Bruhn D1.2 - D1.5** ve **NASA-CR-505** standartlarına uygun analitik havacılık bağlantı kulağı tasarımı ve doğrulaması sunar.

### B-Rep Standart Geometrisi
- Taban plakası birleşiminde gerilme yığılmasını önleyen kök radyusu (`root_fillet`).
- Eğik yükleme açısı ($\theta$) analizi.

### Mühendislik Doğrulama Formülleri
1. **Çekme ve Yataklama Gerilmesi ($K_{tu}$ Analitik Eğrisi):**
   $$F_{tu,\text{lug}} = K_{tu} \cdot F_{tu}$$
   - Bruhn D1.2 analitik eğrisi: $W/D$ oranı ve $F_{ty}/F_{tu}$ malzeme oranına bağlı ampirik formülasyon.

2. **Enine Yükleme (Transverse Shear & Bending - Bruhn D1.3):**
   $$P_{tru} = K_{tru} \cdot A_{tr} \cdot F_{tu}$$

3. **Eğik Yük Etkileşimi (Bruhn D1.5):**
   Eksenel ($P_a = P \cdot \cos\theta$) ve enine ($P_{tr} = P \cdot \sin\theta$) yüklerin süperpozisyonu:
   $$R_a = \frac{P_a}{P_{au}}, \quad R_{tr} = \frac{P_{tr}}{P_{tru}}$$
   $$(R_a)^{1.6} + (R_{tr})^{1.6} \le 1.0$$
   - Emniyet Marjı: $MS = \frac{1}{\left( R_a^{1.6} + R_{tr}^{1.6} \right)^{1/1.6}} - 1.0$
