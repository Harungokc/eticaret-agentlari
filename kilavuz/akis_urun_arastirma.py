"""Ürün Araştırma Agent'ı için hareketli akış şeması (GIF) üretir. Pillow gerekir.

Akış yukarıdan aşağı ilerler: çizgi adım adım dolar, sırası gelen adım belirginleşir, sayılar sayarak gelir.
Rakamlar ve örnek ürünler 13 Ekim 2026'da kaydedilen videodaki mutfak taramasından alınmıştır (RAKAM sözlüğü);
Çin'de fiyatı bulunan ürün sayısı videoda görünmediği için o kartta sayı yerine fiyat vardır. Değiştirirseniz
kaynağını da güncelleyin.

Çalıştırmak için: python kilavuz/akis_urun_arastirma.py çıktı.gif
"""
import math, sys
from PIL import Image, ImageColor, ImageDraw, ImageFont

K, EN, BOY = 2, 1080, 1350
G = "/System/Library/Fonts/Supplemental/Arial.ttf"
B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FON, KUTU, KOYU, ORTA, VURGU = "#F3EEE4", "#E6E4DF", "#2B2B2B", "#8A8782", "#C4532D"
IZ = "#D3D0C9"  # henüz dolmamış akış çizgisi
SONUK = 0.30    # sırası gelmemiş adımın görünürlüğü

RAKAM = {"urun": 135, "yukselen": 24, "cok_satan": 79, "cin_fiyat": "$1.90"}
MESAJ = "Mutfak ürünleri satıyorum. Yurt dışında çok satan ve yükselen ürünleri tara."
KAYNAKLAR = ("Yurt dışı satış raporları", "Video alışveriş listeleri", "Çin üretici dizini")
KARTLAR = (("YÜKSELENLER", "yukselen", "ürün yükselişte", "Işık geçirmez yağ spreyi", ("satışı %200 arttı", "ayda yaklaşık 6.000 adet")),
           ("ÇOK SATANLAR", "cok_satan", "ürün çok satıyor", "Dijital et termometresi", ("ayda yaklaşık 60.000 adet", "yurt dışı fiyatı $13.97")),
           ("ÇİN'DE TEDARİK", "cin_fiyat", "örnek fabrika liste fiyatı", "Titanyum kesme tahtası", (("Yurt dışı", "$29.99-69.99"), ("Çin fabrika", "$1.90-13.50"))))


def karis(a, b, o):
    a, b = ImageColor.getrgb(a), ImageColor.getrgb(b)
    return tuple(round(x * o + y * (1 - o)) for x, y in zip(a, b))
def f(boyut, kalin=False): return ImageFont.truetype(B if kalin else G, int(boyut * K))
def k(*v): return [x * K for x in v]
def genislik(metin, boyut, kalin=False): return f(boyut, kalin).getlength(metin) / K
def yaz(d, x, y, metin, boyut, renk, kalin=False, hiza="sol"):
    font = f(boyut, kalin); g = d.textlength(metin, font=font)
    d.text((x * K - (g / 2 if hiza == "orta" else g if hiza == "sag" else 0), y * K), metin, font=font, fill=renk)
    return g / K
def bezier(p0, p3, n=40):
    (x0, y0), (x3, y3) = p0, p3; ym = (y0 + y3) / 2
    return [((1-t)**3*x0 + 3*(1-t)**2*t*x0 + 3*(1-t)*t*t*x3 + t**3*x3,
             (1-t)**3*y0 + 3*(1-t)**2*t*ym + 3*(1-t)*t*t*ym + t**3*y3) for t in (i / n for i in range(n + 1))]
def esit(yol, aralik=2.0):
    cikti, kalan = [yol[0]], aralik
    for (x0, y0), (x1, y1) in zip(yol, yol[1:]):
        uz = math.hypot(x1 - x0, y1 - y0); yer = 0
        while uz - yer >= kalan:
            yer += kalan; kalan = aralik
            cikti.append((x0 + (x1 - x0) * yer / uz, y0 + (y1 - y0) * yer / uz))
        kalan -= uz - yer
    return cikti
def oran(t, bas, son): return min(1.0, max(0.0, (t - bas) / (son - bas)))
def yumusak(x): return x * x * (3 - 2 * x)
def binlik(n): return f"{n:,}".replace(",", ".")


# ---- yerleşim
A, BK, C, D = (60, 190, 1020, 330), (60, 384, 1020, 548), (230, 602, 850, 666), (60, 1066, 1020, 1210)
KX = [(60, 368), (386, 694), (712, 1020)]; KY0, KY1 = 754, 1010
MERKEZ = [(a + b) / 2 for a, b in KX]
CIP = [(150, 420), (435, 705), (720, 990)]; CY0, CY1 = 468, 520

# ---- zaman çizelgesi (0-1): (başlangıç, bitiş)
Z = {"yaz": (0.02, 0.15), "hatA": (0.16, 0.21), "adim2": 0.21, "cip": (0.23, 0.38), "hatB": (0.40, 0.45), "adim3": 0.45,
     "hatC": (0.50, 0.59), "kart": 0.59, "say": (0.60, 0.74), "hatD": (0.76, 0.84), "adim4": 0.84}
KARE, SURE, BEKLE = 78, 70, 2600

hatlar = {"hatA": [esit([(540, A[3]), (540, BK[1])])], "hatB": [esit([(540, BK[3]), (540, C[1])])],
          "hatC": [esit(bezier((540 + (i - 1) * 150, C[3]), (cx, KY0))) for i, cx in enumerate(MERKEZ)],
          "hatD": [esit(bezier((cx, KY1), (540 + (i - 1) * 220, D[1]))) for i, cx in enumerate(MERKEZ)]}

# ---- değişmeyen zemin: başlık, altlık, boş akış çizgileri
taban = Image.new("RGB", (EN * K, BOY * K), FON)
d = ImageDraw.Draw(taban)
yaz(d, 60, 50, "ÜRÜN ARAŞTIRMA AGENT'I", 16, ORTA, True)
BASLIK = "Yurt dışında ne satıyor, Çin'den kaça gelir?"
boyut = 50
while genislik(BASLIK, boyut, True) > 960: boyut -= 1
yaz(d, 60, 80, BASLIK, boyut, KOYU, True)
yaz(d, 60, 142, "Alanınızı yazarsınız; çok satanları, yükselenleri ve Çin'deki fabrika fiyatını raporlar.", 21, ORTA)
yaz(d, 60, 1266, "Harun Gökce  ·  github.com/Harungokc/eticaret-agentlari", 18, ORTA)
yaz(d, 1020, 1267, "13 Ekim 2026 mutfak taraması · satış adetleri tahmindir", 16, ORTA, hiza="sag")
for yollar in hatlar.values():
    for yol in yollar:
        d.line([(x * K, y * K) for x, y in yol], fill=IZ, width=4 * K, joint="curve")


def katman():
    im = Image.new("RGBA", taban.size, (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
def kutu(o, x0, y0, x1, y1, renk=KUTU, r=20): o.rounded_rectangle(k(x0, y0, x1, y1), radius=r * K, fill=renk)
def numara(o, x, y, no, ters=False):
    o.ellipse(k(x - 22, y - 22, x + 22, y + 22), fill=FON if ters else VURGU)
    yaz(o, x, y - 14, str(no), 24, VURGU if ters else FON, True, "orta")


# ---- adım katmanları (sayı ve yazılan metin dışındaki her şey)
k1, o = katman()
kutu(o, *A); numara(o, 110, A[1] + 40, 1)
yaz(o, 150, A[1] + 25, "Alanınızı yazarsınız", 26, KOYU, True)
yaz(o, 990, A[1] + 29, "Claude ya da ChatGPT sohbetinde", 20, ORTA, hiza="sag")
o.rounded_rectangle(k(150, A[1] + 76, 990, A[1] + 122), radius=14 * K, fill=FON)

k2, o = katman()
kutu(o, *BK); numara(o, 110, BK[1] + 40, 2)
yaz(o, 150, BK[1] + 25, "Asistan internette tarar", 26, KOYU, True)
for (a, b), ad in zip(CIP, KAYNAKLAR):
    o.rounded_rectangle(k(a, CY0, b, CY1), radius=14 * K, fill=FON)
    yaz(o, (a + b) / 2, CY0 + 16, ad, 17, KOYU, True, "orta")

k3, o = katman()
kutu(o, *C, renk=KOYU, r=32); numara(o, C[0] + 40, (C[1] + C[3]) / 2, 3, ters=True)
yaz(o, C[0] + 78, C[1] + 18, "Agent puanlar ve raporu yazar", 24, FON, True)

kk, o = katman()
for (a, b), (ad, _, alt, urun, satirlar) in zip(KX, KARTLAR):
    kutu(o, a, KY0, b, KY1, r=18)
    yaz(o, a + 20, KY0 + 18, ad, 14, ORTA, True)
    yaz(o, a + 20, KY0 + 104, alt, 17, ORTA)
    o.line(k(a + 20, KY0 + 142, b - 20, KY0 + 142), fill=karis(ORTA, KUTU, 0.3), width=K)
    yaz(o, a + 20, KY0 + 158, urun, 18, KOYU, True)
    for j, satir in enumerate(satirlar):
        y = KY0 + 190 + j * 27
        if isinstance(satir, tuple):
            yaz(o, a + 20, y, satir[0], 16, ORTA)
            yaz(o, b - 20, y - (1 if j else 0), satir[1], 17 if j else 16, VURGU if j else KOYU, True, "sag")
        else:
            yaz(o, a + 20, y, satir, 16, ORTA)

k4, o = katman()
kutu(o, *D); numara(o, 110, D[1] + 40, 4)
yaz(o, 150, D[1] + 25, "Raporu alırsınız", 26, KOYU, True)
yaz(o, 990, D[1] + 29, "Rapor sayfası + Excel", 20, ORTA, hiza="sag")
yaz(o, 150, D[1] + 72, "Her üründe fotoğraf, fiyat, kaynak ve tek tıkla arama:", 20, KOYU)
yaz(o, 150, D[1] + 102, "ürün sayfası  ·  1688  ·  Taobao  ·  Alibaba  ·  Trendyol  ·  Hepsiburada", 19, ORTA, True)


def bindir(c, kat, gorunurluk):
    if gorunurluk >= 0.999:
        c.paste(kat, (0, 0), kat); return
    alfa = kat.getchannel("A").point(lambda v: int(v * gorunurluk))
    c.paste(kat, (0, 0), alfa)

def acik(t, bas): return SONUK + (1 - SONUK) * yumusak(oran(t, bas, bas + 0.035))
def soluk(renk, zemin, g): return karis(renk, zemin, g)

def akit(cd, yol, p, bitti, t, kaydir=0.0):
    """Akış çizgisini p oranına kadar doldurur; ucu parlak bir nokta taşır. Dolduktan sonra üstünde küçük noktalar akar."""
    n = max(1, int(p * (len(yol) - 1)))
    if p > 0:
        cd.line([(x * K, y * K) for x, y in yol[:n + 1]], fill=VURGU, width=5 * K, joint="curve")
    if 0 < p < 1:
        x, y = yol[n]
        cd.ellipse(k(x - 17, y - 17, x + 17, y + 17), fill=karis(VURGU, FON, 0.28))
        cd.ellipse(k(x - 10, y - 10, x + 10, y + 10), fill=VURGU, outline=FON, width=2 * K)
    elif bitti:
        q = (t * 5 + kaydir) % 1
        x, y = yol[int(q * (len(yol) - 1))]
        cd.ellipse(k(x - 8, y - 8, x + 8, y + 8), fill=VURGU, outline=FON, width=2 * K)


def kare_ciz(t):
    c = taban.copy(); cd = ImageDraw.Draw(c)
    for ad, yollar in hatlar.items():
        p = yumusak(oran(t, *Z[ad]))
        for j, yol in enumerate(yollar):
            akit(cd, yol, p, t >= Z[ad][1], t, j * 0.37)
    g1, g2, g3, gk, g4 = 1.0, acik(t, Z["adim2"]), acik(t, Z["adim3"]), acik(t, Z["kart"]), acik(t, Z["adim4"])
    for kat, g in ((k1, g1), (k2, g2), (k3, g3), (kk, gk), (k4, g4)):
        bindir(c, kat, g)
    cd = ImageDraw.Draw(c)

    # 1: mesaj harf harf yazılır
    n = round(len(MESAJ) * oran(t, *Z["yaz"]))
    g = yaz(cd, 170, A[1] + 88, MESAJ[:n], 19, KOYU)
    if n < len(MESAJ) or int(t * KARE) % 6 < 3:
        cd.rectangle(k(172 + g, A[1] + 87, 174 + g, A[1] + 111), fill=VURGU)

    # 2: kaynaklar sırayla taranır, bulunan ürün sayısı artar
    cp = oran(t, *Z["cip"])
    for j, (a, b) in enumerate(CIP):
        yerel = oran(cp, j / 3, (j + 1) / 3)
        if yerel > 0:
            renk = VURGU if yerel < 1 else karis(VURGU, FON, 0.75)
            cd.rounded_rectangle(k(a, CY0, b, CY1), radius=14 * K, outline=renk, width=3 * K)
            if yerel < 1:  # tarama çubuğu
                x = a + 14 + (b - a - 28) * yerel
                cd.line(k(a + 14, CY1 - 7, x, CY1 - 7), fill=VURGU, width=3 * K)
    bulunan = round(RAKAM["urun"] * yumusak(cp))
    if t >= Z["adim2"]:
        w = yaz(cd, 990, BK[1] + 29, " ürün bulundu", 20, soluk(ORTA, KUTU, g2), hiza="sag")
        yaz(cd, 990 - w, BK[1] + 27, str(bulunan), 22, soluk(VURGU if cp < 1 else KOYU, KUTU, g2), True, "sag")

    # sonuç kartları: sayılar sayarak gelir
    sp = yumusak(oran(t, *Z["say"]))
    for (a, b), (_, anahtar, *_r) in zip(KX, KARTLAR):
        hedef = RAKAM[anahtar]
        if isinstance(hedef, str):  # sayılmayan değer (fiyat): sayım bitince görünür
            metin = hedef if sp >= 1 else ""
        else:
            metin = binlik(round(hedef * sp) if t >= Z["kart"] else 0)
        yaz(cd, a + 20, KY0 + 40, metin, 56, soluk(VURGU if 0 < sp < 1 else KOYU, KUTU, gk), True)
    return c.resize((EN, BOY), Image.LANCZOS)


kareler = [kare_ciz(n / (KARE - 1)) for n in range(KARE)]
# Son kare (her şey açık) uzun bekler; paylaşımın küçük resmi de odur.
ornek = Image.new("RGB", (len(kareler), 1))
pal_kaynak = Image.new("RGB", (EN, BOY * 2)); pal_kaynak.paste(kareler[-1], (0, 0)); pal_kaynak.paste(kareler[KARE // 2], (0, BOY))
pal = pal_kaynak.quantize(colors=96, method=Image.MEDIANCUT, dither=Image.Dither.NONE).getpalette()[:288]
for r in (FON, KUTU, KOYU, ORTA, VURGU, IZ): pal += list(ImageColor.getrgb(r))
palet = Image.new("P", (1, 1)); palet.putpalette(pal + [0] * (768 - len(pal)))
gif = [kr.quantize(palette=palet, dither=Image.Dither.NONE) for kr in kareler]
gif[0].save(sys.argv[1], save_all=True, append_images=gif[1:], duration=[SURE] * (KARE - 1) + [BEKLE], loop=0, optimize=False)
kareler[-1].save(sys.argv[1].replace(".gif", ".png"))
for ad, n in (("-kare-a", int(KARE * 0.30)), ("-kare-b", int(KARE * 0.55)), ("-kare-c", int(KARE * 0.68))):
    kareler[n].save(sys.argv[1].replace(".gif", ad + ".png"))
print("kare:", KARE, "süre (sn):", round((SURE * (KARE - 1) + BEKLE) / 1000, 1))
