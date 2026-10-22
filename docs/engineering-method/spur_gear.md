# Düz Alın Dişlisi (Involute Spur Gear)

## 1. Yöntem ve Standartlar
Bu şablon, AGMA 2001-D04 ve ISO 6336 standartlarına dayalı olarak $20^\circ$ kavrama açılı standart evolvent düz dişli geometrisi üretir.

### Uygulanan Formüller
1. **Lewis Diş Kökü Eğilme Gerilmesi ($\sigma_b$):**
   $$F_t = \frac{2 \cdot T}{d_{\text{pitch}}}$$
   $$\sigma_b = \frac{F_t}{b \cdot m \cdot Y}$$
   - $F_t$: Teğetsel diş kuvveti ($N$)
   - $m$: Modül ($mm$)
   - $b$: Diş genişliği ($mm$)
   - $Y$: Lewis form faktörü ($Y \approx 0.154 - \frac{0.912}{z}$)

2. **Alt Kesilme (Undercut) Sınırı:**
   - Standart $20^\circ$ kavrama açısında alt kesilmeyi önlemek için $z \ge 17$ kuralı denetlenir.

3. **Emniyet Marjı ($MS$):**
   $$MS = \frac{\sigma_{\text{allow}}}{FoS \cdot \sigma_b} - 1.0$$
