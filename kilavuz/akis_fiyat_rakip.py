"""Ürün, Fiyat ve Rakip Analizcisi için hareketli akış şeması (GIF) üretir. Pillow gerekir.

Çalıştırmak için: python kilavuz/akis_fiyat_rakip.py 02-urun-fiyat-ve-rakip-analizcisi/ornek/ornek_urunler.csv çıktı.gif
"""
import csv, math, statistics, sys
from PIL import Image, ImageColor, ImageDraw, ImageFont

K, EN, BOY = 2, 1080, 1350
G = "/System/Library/Fonts/Supplemental/Arial.ttf"
B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FON, KUTU, KOYU, ORTA = "#F3EEE4", "#E6E4DF", "#2B2B2B", "#8A8782"

def karis(a, b, o):
    a, b = ImageColor.getrgb(a), ImageColor.getrgb(b)
    return tuple(round(x * o + y * (1 - o)) for x, y in zip(a, b))
def sayi(s): return float(s.replace(".", "").replace(",", "."))
def tl(v): return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"

with open(sys.argv[1], encoding="utf-8-sig") as dosya:
    satirlar = list(csv.DictReader(dosya, delimiter=";"))
ben = next(s for s in satirlar if s["benim"]); rakipler = [s for s in satirlar if not s["benim"]]
bf = sayi(ben["fiyat"]); rf = sorted(sayi(r["fiyat"]) for r in rakipler)
ucuz, pahali, ortanca = sum(r < bf for r in rf), sum(r > bf for r in rf), statistics.median(rf)
print("rakam:", tl(bf), len(rf), tl(ortanca), ucuz, pahali, tl(rf[0]), tl(rf[-1]))

def f(boyut, kalin=False): return ImageFont.truetype(B if kalin else G, int(boyut * K))
def k(*v): return [x * K for x in v]
def yaz(d, x, y, metin, boyut, renk, kalin=False, hiza="sol"):
    font = f(boyut, kalin); g = d.textlength(metin, font=font)
    d.text((x * K - (g / 2 if hiza == "orta" else g if hiza == "sag" else 0), y * K), metin, font=font, fill=renk)
    return g / K
def numara(d, x, y, no, ters=False):
    d.ellipse(k(x - 22, y - 22, x + 22, y + 22), fill=FON if ters else KOYU)
    yaz(d, x, y - 14, str(no), 24, KOYU if ters else FON, True, "orta")
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

A, BP, CP, D = (60, 186, 1020, 452), (250, 506, 830, 570), (250, 624, 830, 688), (60, 1076, 1020, 1226)
KX = [(60, 368), (386, 694), (712, 1020)]; KY0, KY1 = 778, 1000
MERKEZ = [(a + b) / 2 for a, b in KX]

taban = Image.new("RGB", (EN * K, BOY * K), FON)
d = ImageDraw.Draw(taban)
yaz(d, 60, 50, "ÜRÜN, FİYAT VE RAKİP ANALİZCİSİ", 16, ORTA, True)
yaz(d, 60, 78, "Fiyatınız pazarda nerede duruyor?", 50, KOYU, True)
yaz(d, 60, 144, "Rakip listesini verirsiniz; fiyatınızın yerini ve geride kaldığınız noktaları hesaplar.", 21, ORTA)

yollar = [[(540, A[3]), (540, BP[1])], [(540, BP[3]), (540, CP[1])]]
for i, cx in enumerate(MERKEZ):
    yollar.append(bezier((540 + (i - 1) * 150, CP[3]), (cx, KY0)))
    yollar.append(bezier((cx, KY1), (540 + (i - 1) * 220, D[1])))
yollar = [esit(y) for y in yollar]
for yol in yollar:
    d.line([(x * K, y * K) for x, y in yol], fill=ORTA, width=3 * K, joint="curve")

on = Image.new("RGBA", taban.size, (0, 0, 0, 0)); o = ImageDraw.Draw(on)
def kutu(x0, y0, x1, y1, renk=KUTU, r=20): o.rounded_rectangle(k(x0, y0, x1, y1), radius=r * K, fill=renk)

# 1 — liste
kutu(*A); numara(o, 110, A[1] + 40, 1)
yaz(o, 150, A[1] + 25, "Rakip listesini verirsiniz", 26, KOYU, True)
yaz(o, 990, A[1] + 29, f"Sizin ürününüz + {len(rakipler)} rakip", 20, ORTA, hiza="sag")
SUTUN = [(166, "sol"), (590, "sag"), (700, "sag"), (810, "sag"), (974, "sag")]
tablo = [("Ürün", "Fiyat", "Puan", "Yorum", "Kargo"), ("Sizin ürününüz", ben["fiyat"], ben["puan"], ben["yorum"], ben["kargo"])] + \
        [(f"Rakip {j + 1}", r["fiyat"], r["puan"], r["yorum"], r["kargo"]) for j, r in enumerate(rakipler[:3])]
for j, satir in enumerate(tablo):
    y = A[1] + 78 + j * 36
    if j == 1: o.rounded_rectangle(k(150, y - 3, 990, y + 31), radius=8 * K, fill=KOYU)
    elif 1 < j < 4: o.line(k(150, y + 32, 990, y + 32), fill=karis(ORTA, KUTU, 0.3), width=K)
    for (x, hiza), hucre in zip(SUTUN, satir):
        yaz(o, x, y + 4, hucre, 15 if j == 0 else 18, ORTA if j == 0 else FON if j == 1 else KOYU, j < 2, hiza)
# 2 ve 3 — düğümler
kutu(*BP, r=32); numara(o, BP[0] + 40, (BP[1] + BP[3]) / 2, 2)
yaz(o, BP[0] + 78, BP[1] + 18, "Claude ya da ChatGPT'ye yüklersiniz", 24, KOYU, True)
kutu(*CP, renk=KOYU, r=32); numara(o, CP[0] + 40, (CP[1] + CP[3]) / 2, 3, ters=True)
yaz(o, CP[0] + 78, CP[1] + 18, "Agent üç şeyi hesaplar", 24, FON, True)
# üç sonuç
for (a, b), ad in zip(KX, ("PAZAR ORTALAMASI", "FİYAT KONUMU", "RAKİP KARŞILAŞTIRMA")):
    kutu(a, KY0, b, KY1, r=18); yaz(o, a + 20, KY0 + 18, ad, 14, ORTA, True)
a, b = KX[0]
yaz(o, a + 20, KY0 + 46, tl(ortanca), 36, KOYU, True); yaz(o, a + 20, KY0 + 92, "ortanca fiyat", 17, ORTA)
for j, (ad, deger) in enumerate((("En düşük", tl(rf[0])), ("En yüksek", tl(rf[-1])))):
    y = KY0 + 142 + j * 34
    o.line(k(a + 20, y - 9, b - 20, y - 9), fill=karis(ORTA, KUTU, 0.3), width=K)
    yaz(o, a + 20, y, ad, 17, ORTA); yaz(o, b - 20, y, deger, 17, KOYU, True, "sag")
a, b = KX[1]
yaz(o, a + 20, KY0 + 46, f"{ucuz} / {pahali}", 36, KOYU, True); yaz(o, a + 20, KY0 + 92, "ürün sizden ucuz / pahalı", 17, ORTA)
SX0, SX1, SY = a + 26, b - 26, KY0 + 172
def sx(v): return SX0 + (v - rf[0]) / (rf[-1] - rf[0]) * (SX1 - SX0)
o.line(k(SX0, SY, SX1, SY), fill=karis(ORTA, KUTU, 0.4), width=3 * K)
for v in rf: o.ellipse(k(sx(v) - 5, SY - 5, sx(v) + 5, SY + 5), fill=ORTA)
yaz(o, SX0, SY + 16, "en ucuz", 14, ORTA); yaz(o, SX1, SY + 16, "en pahalı", 14, ORTA, hiza="sag")
BX = sx(bf); yaz(o, BX, SY - 42, "siz", 16, KOYU, True, "orta")
a, b = KX[2]
for j, (ad, durum) in enumerate((("Fiyat", "geride"), ("Yorum sayısı", "geride"), ("Favori sayısı", "geride"), ("Kargo", "geride"), ("Puan", "aynı"))):
    y = KY0 + 46 + j * 33
    yaz(o, a + 20, y + 3, ad, 17, KOYU)
    if durum == "geride": o.rounded_rectangle(k(b - 100, y, b - 20, y + 26), radius=13 * K, fill=KOYU)
    else: o.rounded_rectangle(k(b - 100, y, b - 20, y + 26), radius=13 * K, outline=ORTA, width=2 * K)
    yaz(o, b - 60, y + 5, durum, 15, FON if durum == "geride" else ORTA, True, "orta")
# 4 — sonuç
kutu(*D); numara(o, 110, D[1] + 40, 4)
yaz(o, 150, D[1] + 25, "Sonucu alırsınız", 26, KOYU, True)
yaz(o, 990, D[1] + 29, "Türkçe açıklama + Excel raporu", 20, ORTA, hiza="sag")
yaz(o, 150, D[1] + 74, "“Fiyatınız pazar ortancasının %5 üstünde. Yorum, favori ve kargoda", 20, KOYU)
yaz(o, 150, D[1] + 102, "rakiplerin gerisindesiniz.”", 20, KOYU)
yaz(o, 60, 1282, "Harun Gökce  ·  github.com/Harungokc/eticaret-agentlari", 18, ORTA)
yaz(o, 1020, 1282, "Rakamlar örnek veridir (500 ml çelik termos)", 18, ORTA, hiza="sag")

KARE = 30
HALE = karis(KOYU, FON, 0.2)
kareler = []
for n in range(KARE):
    c = taban.copy(); cd = ImageDraw.Draw(c); t = n / KARE
    for j, yol in enumerate(yollar):
        adet = max(1, round(len(yol) * 2 / 80))
        for m in range(adet):
            p = ((m + t) / adet + j * 0.11) % 1
            x, y = yol[int(p * (len(yol) - 1))]
            cd.ellipse(k(x - 15, y - 15, x + 15, y + 15), fill=HALE)
            cd.ellipse(k(x - 9, y - 9, x + 9, y + 9), fill=KOYU, outline=FON, width=2 * K)
    c.paste(on, (0, 0), on); cd = ImageDraw.Draw(c)
    for fz in (t, (t + 0.5) % 1):
        r = 10 + fz * 14
        cd.ellipse(k(BX - r, SY - r, BX + r, SY + r), outline=karis(KOYU, KUTU, 0.6 * (1 - fz)), width=2 * K)
    cd.ellipse(k(BX - 10, SY - 10, BX + 10, SY + 10), fill=KOYU, outline=KUTU, width=2 * K)
    kareler.append(c.resize((EN, BOY), Image.LANCZOS))

pal = kareler[0].quantize(colors=64, method=Image.MEDIANCUT, dither=Image.Dither.NONE).getpalette()[:192]
for r in (FON, KUTU, KOYU, ORTA): pal += list(ImageColor.getrgb(r))
pal += list(HALE)
palet = Image.new("P", (1, 1)); palet.putpalette(pal + [0] * (768 - len(pal)))
gif = [kr.quantize(palette=palet, dither=Image.Dither.NONE) for kr in kareler]
gif[0].save(sys.argv[2], save_all=True, append_images=gif[1:], duration=66, loop=0)
kareler[7].save(sys.argv[2].replace(".gif", ".png"))
