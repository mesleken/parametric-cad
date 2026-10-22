# Kademeli İletim Mili (Stepped Transmission Shaft)

## 1. Yöntem ve Standartlar
Kademeli güç iletim milleri, torku iletirken yataklama ve eksenel konumlandırma için faturalara (shoulder) ihtiyaç duyar.
Bu şablon DIN 6885 Form A kama yuvası ve gerilme yığılması analizini kapsar.

### Uygulanan Formüller
1. **Burulma Kayma Gerilmesi ($\tau$):**
   $$\tau = \frac{16 \cdot T}{\pi \cdot d_1^3}$$
   - $T$: İletilen tork ($N \cdot mm$)
   - $d_1$: En küçük mil çapı ($mm$)

2. **Fatura Geçiş Radyusu Oranı ($r / d_1$):**
   - $r / d_1 \ge 0.05$ kuralı ile çentik faktörü $K_t \le 1.8$ mertebesinde tutulur.
   - Yorulma kırılmalarını önlemek için DIN 743 ve Peterson standartlarına uygundur.

3. **Emniyet Marjı ($MS$):**
   $$MS = \frac{\tau_{\text{yield}}}{FoS \cdot \tau_{\text{applied}}} - 1.0$$
