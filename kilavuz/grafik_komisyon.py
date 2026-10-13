"""Pazar ve Komisyon Analizcisi için hareketli görsel (GIF) üretir. Pillow gerekir.

Tek cümle yazılır; sonra aynı 899 TL'lik ürün üç pazaryerinde sırayla "kesilir": şerit satış fiyatıdır,
sağdan komisyon ayrılır, elinize geçen tutar sayarak aşağı iner.
Rakamlar aracın şu komutunun çıktısıdır (komisyon tablosu derlemesi: 8 Ekim 2026), kuruşlar yuvarlanmıştır:
    python agent.py komisyon Ayakkabı 899 --maliyet 400
Tabloyu ya da örneği değiştirirseniz PAZARYERLERI ve SONUC'u da güncelleyin.

Çalıştırmak için: python kilavuz/grafik_komisyon.py çıktı.gif
"""
import sys
from PIL import Image, ImageColor, ImageDraw, ImageFont

K, EN, BOY = 2, 1080, 1350
G = "/System/Library/Fonts/Supplemental/Arial.ttf"
B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FON, KUTU, KOYU, ORTA, VURGU = "#F3EEE4", "#E6E4DF", "#2B2B2B", "#8A8782", "#C4532D"

FIYAT, MALIYET = 899, 400
MESAJ = "899 TL'lik ayakkabıyı hangi pazaryerinde satmalıyım? Maliyetim 400 TL."
# (pazaryeri, komisyon oranı, ele geçen en az, ele geçen en çok, kesinti yazısı)
PAZARYERLERI = (("Hepsiburada", "%18 – %19,49", 723.78, 737.18, "komisyon 162 – 175 TL"),
                ("n11", "%15 – %20,34", 698.16, 746.17, "komisyon 135 – 183 TL + hizmet bedeli"),
                ("Trendyol", "%21,5 – %22,5", 696.72, 705.72, "komisyon 193 – 202 TL"))
SONUC = ("Ortalamada Hepsiburada önde; n11 ile aralıklar çakışıyor.",
         "Kesin sıra için kendi sözleşme oranınızı girersiniz.")
KART_Y, KART, ARA = 312, 252, 22      # ilk kartın üstü, kart yüksekliği, aralık
X0, X1 = 84, 996                      # şeridin sol ve sağ kenarı (tamamı = satış fiyatı)
Z = {"yaz": (0.02, 0.14), "kart": (0.17, 0.86), "sonuc": (0.88, 0.96)}
KARE, SURE, BEKLE = 90, 70, 3200


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
def tl(a, b): return f"{round(a)} TL" if round(a) == round(b) else f"{round(a)} – {round(b)} TL"


ACIK = "#%02X%02X%02X" % karis(VURGU, KUTU, 0.42)       # orana göre değişen kısım

# ---- değişmeyen zemin
taban = Image.new("RGB", (EN * K, BOY * K), FON)
d = ImageDraw.Draw(taban)
yaz(d, 60, 50, "PAZAR VE KOMİSYON ANALİZCİSİ", 16, ORTA, True)
yaz(d, 60, 80, "Aynı ürün, aynı fiyat.", 50, KOYU, True)
yaz(d, 60, 138, "Elinize kalan aynı değil.", 50, VURGU, True)
d.rounded_rectangle(k(60, 216, 1020, 280), radius=18 * K, fill=KUTU)
yaz(d, 60, 1218, "Oranlar yaklaşıktır (derleme: 8 Ekim 2026); açık renkli bölüm orana göre değişen kısımdır.", 17, ORTA)
yaz(d, 60, 1242, "Kargo, sabit hizmet bedeli, KDV, reklam ve iade hesaba dahil değildir. Kuruşlar yuvarlandı.", 17, ORTA)
yaz(d, 60, 1292, "Harun Gökce  ·  github.com/Harungokc/eticaret-agentlari", 18, ORTA)


def kare_ciz(t):
    c = taban.copy(); cd = ImageDraw.Draw(c)

    # mesaj harf harf yazılır
    n = round(len(MESAJ) * oran(t, *Z["yaz"]))
    g = yaz(cd, 86, 236, MESAJ[:n], 21, KOYU)
    if n < len(MESAJ) or int(t * KARE) % 6 < 3:
        cd.rectangle(k(88 + g, 235, 90 + g, 261), fill=VURGU)

    # kartlar sırayla gelir: önce şerit tam (satış fiyatı), sonra komisyon sağdan kesilir
    kp = oran(t, *Z["kart"])
    for j, (ad, oran_yazi, en_az, en_cok, kesinti) in enumerate(PAZARYERLERI):
        y = KART_Y + j * (KART + ARA)
        yerel = oran(kp, j / len(PAZARYERLERI), (j + 1) / len(PAZARYERLERI))
        g1 = yumusak(oran(yerel, 0.0, 0.22))      # kart ve tam şerit
        g2 = yumusak(oran(yerel, 0.32, 0.80))     # kesinti
        g3 = yumusak(oran(yerel, 0.80, 1.0))      # alt yazılar
        cd.rounded_rectangle(k(60, y, 1020, y + KART), radius=18 * K, fill=karis(KUTU, FON, 0.25 + 0.75 * g1))
        if g1 <= 0:
            continue
        yaz(cd, X0, y + 26, ad, 36, karis(KOYU, KUTU, g1), True)
        yaz(cd, X0, y + 76, "Komisyon oranı  " + oran_yazi, 21, karis(ORTA, KUTU, g1))
        a, b = FIYAT - (FIYAT - en_az) * g2, FIYAT - (FIYAT - en_cok) * g2
        yaz(cd, X1, y + 22, "ELİNİZE GEÇEN", 15, karis(ORTA, KUTU, g1), True, "sag")
        yaz(cd, X1, y + 44, tl(a, b), 46, karis(KOYU, KUTU, g1), True, "sag")

        # şerit: koyu = elinize geçen, açık = orana göre değişen, vurgu = kesilen
        px = lambda tutar: X0 + (X1 - X0) * tutar / FIYAT
        sy = y + 124
        cd.rounded_rectangle(k(X0, sy, X1, sy + 44), radius=10 * K, fill=karis(VURGU, KUTU, g1))
        cd.rectangle(k(px(a) - 12, sy, px(b), sy + 44), fill=karis(ACIK, KUTU, g1))
        cd.rounded_rectangle(k(X0, sy, px(a), sy + 44), radius=10 * K, fill=karis(KOYU, KUTU, g1))
        cd.rectangle(k(px(a) - 12, sy, px(a), sy + 44), fill=karis(KOYU, KUTU, g1))
        if g3 > 0:
            kar = tl(en_az - MALIYET, en_cok - MALIYET)
            w = yaz(cd, X0, sy + 62, "Kârınız  ", 21, karis(ORTA, KUTU, g3))
            yaz(cd, X0 + w, sy + 60, kar, 23, karis(KOYU, KUTU, g3), True)
            yaz(cd, X1, sy + 62, "Kesilen: " + kesinti, 21, karis(VURGU, KUTU, g3), True, "sag")

    sp = yumusak(oran(t, *Z["sonuc"]))
    if sp > 0:
        yaz(cd, 60, 1140, SONUC[0], 24, karis(KOYU, FON, sp), True)
        yaz(cd, 60, 1174, SONUC[1], 22, karis(ORTA, FON, sp))
    return c.resize((EN, BOY), Image.LANCZOS)


kareler = [kare_ciz(n / (KARE - 1)) for n in range(KARE)]
# Son kare (her şey açık) uzun bekler; paylaşımın küçük resmi de odur.
pal_kaynak = Image.new("RGB", (EN, BOY * 2)); pal_kaynak.paste(kareler[-1], (0, 0)); pal_kaynak.paste(kareler[KARE // 2], (0, BOY))
pal = pal_kaynak.quantize(colors=96, method=Image.MEDIANCUT, dither=Image.Dither.NONE).getpalette()[:288]
for r in (FON, KUTU, KOYU, ORTA, VURGU): pal += list(ImageColor.getrgb(r))
pal += list(ImageColor.getrgb(ACIK))
palet = Image.new("P", (1, 1)); palet.putpalette(pal + [0] * (768 - len(pal)))
gif = [kr.quantize(palette=palet, dither=Image.Dither.NONE) for kr in kareler]
gif[0].save(sys.argv[1], save_all=True, append_images=gif[1:], duration=[SURE] * (KARE - 1) + [BEKLE], loop=0, optimize=False)
kareler[-1].save(sys.argv[1].replace(".gif", ".png"))
kareler[int(KARE * 0.5)].save(sys.argv[1].replace(".gif", "-ara.png"))
print("kare:", KARE, "süre (sn):", round((SURE * (KARE - 1) + BEKLE) / 1000, 1))
