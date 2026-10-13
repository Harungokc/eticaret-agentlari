"""Ürün Araştırma Agent'ı için hareketli sonuç kartları (GIF) üretir. Pillow gerekir.

Tek cümle yazılır, sayılar sayarak gelir, sonra ürün kartları sırayla açılır: her kartta ürünün yurt dışı
satış fiyatı ve Çin'deki fabrika liste fiyatı yan yana durur.
Ürünler ve rakamlar 13 Ekim 2026'da kaydedilen videoda sohbet ekranında görünen tablolardan alınmıştır
(RAKAM ve BOLUMLER); değiştirirseniz kaynağını da güncelleyin.

Çalıştırmak için: python kilavuz/grafik_urun_arastirma.py çıktı.gif
"""
import sys
from PIL import Image, ImageColor, ImageDraw, ImageFont

K, EN, BOY = 2, 1080, 1350
G = "/System/Library/Fonts/Supplemental/Arial.ttf"
B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FON, KUTU, KOYU, ORTA, VURGU = "#F3EEE4", "#E6E4DF", "#2B2B2B", "#8A8782", "#C4532D"

RAKAM = (("ürün tarandı", 135), ("yeni yükselen", 24), ("çok satan", 79))
MESAJ = "Mutfak ürünleri satıyorum. Yurt dışında çok satan ve yükselen ürünleri tara."
# (ürün, satış bilgisi, yurt dışı fiyatı, Çin'de fabrika liste fiyatı)
BOLUMLER = (("YENİ YÜKSELENLER", (
                ("Işık geçirmez yağ spreyi", "ayda yaklaşık 6.000 adet  ·  satışı %200 arttı", "$9.99", "$0.62-1.80"),
                ("Titanyum kesme tahtası, 3'lü set", "ayda yaklaşık 5.000 adet  ·  satışı %66,7 arttı", "$59.99", "$1.90-13.50"),
                ("Kapaklı silikon buz kalıbı, 4'lü", "ayda yaklaşık 4.000 adet  ·  satışı %471 arttı", "$6.98", "$0.17-3.70"))),
            ("ÇOK SATANLAR", (
                ("Anında okuyan et termometresi", "ayda yaklaşık 60.000 adet", "$13.97", "$0.60-6.53"),
                ("Hazneli sebze doğrayıcı", "ayda yaklaşık 20.000 adet", "$26.99", "$1.20-7.80"),
                ("2'si 1 arada cam yağ spreyi", "ayda yaklaşık 20.000 adet", "$7.99", "$0.62-1.80"))))
BOLUM_Y = (398, 782)          # bölüm başlıklarının üstü
KART, ARA = 100, 10           # kart yüksekliği ve aralığı
X_YURT, X_CIN = 770, 996      # fiyat sütunlarının sağ kenarı
Z = {"yaz": (0.02, 0.15), "say": (0.16, 0.28), "kart": (0.30, 0.93)}
KARE, SURE, BEKLE = 84, 70, 3000


def karis(a, b, o):
    a, b = ImageColor.getrgb(a), ImageColor.getrgb(b)
    return tuple(round(x * o + y * (1 - o)) for x, y in zip(a, b))
def f(boyut, kalin=False): return ImageFont.truetype(B if kalin else G, int(boyut * K))
def k(*v): return [x * K for x in v]
def yaz(d, x, y, metin, boyut, renk, kalin=False, hiza="sol"):
    font = f(boyut, kalin); g = d.textlength(metin, font=font)
    d.text((x * K - (g / 2 if hiza == "orta" else g if hiza == "sag" else 0), y * K), metin, font=font, fill=renk)
    return g / K
def oran(t, bas, son): return min(1.0, max(0.0, (t - bas) / (son - bas)))
def yumusak(x): return x * x * (3 - 2 * x)


# ---- değişmeyen zemin
taban = Image.new("RGB", (EN * K, BOY * K), FON)
d = ImageDraw.Draw(taban)
yaz(d, 60, 50, "ÜRÜN ARAŞTIRMA AGENT'I", 16, ORTA, True)
yaz(d, 60, 80, "Yurt dışında ne satıyor,", 50, KOYU, True)
yaz(d, 60, 138, "Çin'de fabrika fiyatı ne?", 50, VURGU, True)
d.rounded_rectangle(k(60, 216, 1020, 280), radius=18 * K, fill=KUTU)
for (ad, _), y in zip(BOLUMLER, BOLUM_Y):
    yaz(d, 60, y, ad, 17, ORTA, True)
    yaz(d, X_YURT, y, "Yurt dışı fiyatı", 17, ORTA, hiza="sag")
    yaz(d, X_CIN, y, "Çin'de fabrika", 17, VURGU, True, hiza="sag")
yaz(d, 60, 1190, "Fabrika fiyatı liste fiyatıdır; nakliye, gümrük ve vergi dahil değildir. Satış adetleri tahmindir.", 17, ORTA)
yaz(d, 60, 1266, "Harun Gökce  ·  github.com/Harungokc/eticaret-agentlari", 18, ORTA)
yaz(d, 1020, 1267, "13 Ekim 2026 mutfak taraması", 16, ORTA, hiza="sag")

KARTLAR = [(by + 30 + j * (KART + ARA), u) for (_, urunler), by in zip(BOLUMLER, BOLUM_Y) for j, u in enumerate(urunler)]


def kare_ciz(t):
    c = taban.copy(); cd = ImageDraw.Draw(c)

    # mesaj harf harf yazılır
    n = round(len(MESAJ) * oran(t, *Z["yaz"]))
    g = yaz(cd, 86, 236, MESAJ[:n], 21, KOYU)
    if n < len(MESAJ) or int(t * KARE) % 6 < 3:
        cd.rectangle(k(88 + g, 235, 90 + g, 261), fill=VURGU)

    # sayılar sayarak gelir
    sp = yumusak(oran(t, *Z["say"]))
    for j, (ad, hedef) in enumerate(RAKAM):
        x = 60 + j * 330
        w = yaz(cd, x, 304, str(round(hedef * sp)), 50, VURGU if 0 < sp < 1 else KOYU, True)
        yaz(cd, x + w + 12, 329, ad, 22, karis(ORTA, FON, 0.3 + 0.7 * sp))

    # kartlar sırayla açılır: önce ürün ve yurt dışı fiyatı, sonra Çin fiyatı
    kp = oran(t, *Z["kart"])
    for j, (y, (ad, bilgi, yurt, cin)) in enumerate(KARTLAR):
        yerel = oran(kp, j / len(KARTLAR), (j + 1) / len(KARTLAR))
        g1 = yumusak(oran(yerel, 0.0, 0.30))      # kart, ürün adı, yurt dışı fiyatı
        g2 = yumusak(oran(yerel, 0.50, 0.85))     # Çin fiyatı
        kay = (1 - g1) * 14                       # alttan hafifçe yerine oturur
        cd.rounded_rectangle(k(60, y + kay, 1020, y + KART + kay), radius=18 * K, fill=karis(KUTU, FON, 0.25 + 0.75 * g1))
        if g1 > 0:
            yaz(cd, 84, y + 18 + kay, ad, 25, karis(KOYU, KUTU, g1), True)
            yaz(cd, 84, y + 57 + kay, bilgi, 18, karis(ORTA, KUTU, g1))
            yaz(cd, X_YURT, y + 30 + kay, yurt, 32, karis(KOYU, KUTU, g1), True, "sag")
        if g2 > 0:
            yaz(cd, X_CIN, y + 30 + kay, cin, 32, karis(VURGU, KUTU, g2), True, "sag")
    return c.resize((EN, BOY), Image.LANCZOS)


kareler = [kare_ciz(n / (KARE - 1)) for n in range(KARE)]
# Son kare (her şey açık) uzun bekler; paylaşımın küçük resmi de odur.
pal_kaynak = Image.new("RGB", (EN, BOY * 2)); pal_kaynak.paste(kareler[-1], (0, 0)); pal_kaynak.paste(kareler[KARE // 2], (0, BOY))
pal = pal_kaynak.quantize(colors=96, method=Image.MEDIANCUT, dither=Image.Dither.NONE).getpalette()[:288]
for r in (FON, KUTU, KOYU, ORTA, VURGU): pal += list(ImageColor.getrgb(r))
palet = Image.new("P", (1, 1)); palet.putpalette(pal + [0] * (768 - len(pal)))
gif = [kr.quantize(palette=palet, dither=Image.Dither.NONE) for kr in kareler]
gif[0].save(sys.argv[1], save_all=True, append_images=gif[1:], duration=[SURE] * (KARE - 1) + [BEKLE], loop=0, optimize=False)
kareler[-1].save(sys.argv[1].replace(".gif", ".png"))
kareler[int(KARE * 0.62)].save(sys.argv[1].replace(".gif", "-ara.png"))
print("kare:", KARE, "süre (sn):", round((SURE * (KARE - 1) + BEKLE) / 1000, 1))
