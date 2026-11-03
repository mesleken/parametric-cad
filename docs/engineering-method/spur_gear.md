# Düz Alın Dişlisi (Involute Spur Gear)

## 1. Yöntem ve Standartlar
Bu şablon, **ISO 53**, **ISO 6336-1..5** ve **AGMA 2001-D04** standartlarına uygun evolvent profil geometrisi ve mühendislik analizleri üretir.

### B-Rep Standart Geometrisi
- **Evolvent Eğrisi:** Her diş yanağı için çok noktalı gerçek involute spline interpolasyonu.
- **Profil Ötelemesi (Profile Shift $x$):** Diş başı ve kök dairesi $x \cdot m$ ile ötelenir, diş kalınlığı $s_p = m(\pi/2 + 2x\tan\alpha)$ olarak ayarlanır.
- **DIN 6885-1 Göbek Kaması:** Mil bağlantısı için standart paralel kama kanalı.

### Mühendislik Doğrulama Formülleri
1. **Diş Kökü Eğilme Gerilmesi (ISO 6336 / AGMA + Dolan-Broghamer $K_f$):**
   $$F_t = \frac{2 \cdot T}{d_{\text{pitch}}}$$
   $$\sigma_F = \frac{F_t \cdot K_f}{b \cdot m \cdot Y}$$
   - $K_f$: Dolan-Broghamer kök çentik faktörü ($K_f \approx 0.18 + (t/r_f)^{0.15} \cdot (t/h_f)^{0.45}$)
   - $Y$: Profil ötelemesiyle düzeltilmiş Lewis/AGMA geometri form faktörü

2. **Hertz Yüzey Temas ve Çukurlaşma (Pitting) Gerilmesi (ISO 6336-2):**
   $$\sigma_H = Z_E \cdot Z_H \cdot \sqrt{\frac{F_t}{b \cdot d_p} \cdot \frac{u + 1}{u}}$$
   - $Z_E = \sqrt{\frac{E}{2\pi(1 - \nu^2)}}$: Malzemenin elastisite modülü ve Poisson oranına bağlı elastisite faktörü
   - $Z_H = \sqrt{\frac{2}{\sin(2\alpha)}}$: Bölge faktörü ($20^\circ$ kavrama açısı için $\approx 1.764$)
   - İzin verilen temas yorulma dayanımı $\sigma_{H,\text{lim}} \approx 2.5 \cdot HB + 150 \text{ MPa}$

3. **Alt Kesilme (Undercut) Sınırı:**
   $$z_{\min} = 17 \cdot (1 - x)$$
   - Pozitif profil kaydırma ($x > 0$), $z < 17$ diş sayılarında alt kesilmeyi önler.
