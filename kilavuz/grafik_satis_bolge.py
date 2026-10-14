"""Satış Bölge Analizcisi için hareketli görsel (GIF) üretir. Pillow gerekir.

Üstte sipariş listesi akar ve sayılır (yalnızca il ve ilçe sütunları öne çıkar); altta aynı siparişler
il il, her ilin altında ilçe ilçe çubuklara dönüşür; en altta aracın bir önerisi belirir.
Satırlar ve rakamlar aracın örnek dosyasından (04-satis-bolge-analizcisi/ornek/ornek_siparisler.csv,
400 uydurma sipariş) ve o dosyadaki çıktısından alınmıştır; değiştirirseniz kaynağını da güncelleyin.

Çalıştırmak için: python kilavuz/grafik_satis_bolge.py çıktı.gif
"""
import sys
from PIL import Image, ImageColor, ImageDraw, ImageFont

K, EN, BOY = 2, 1080, 1350
G = "/System/Library/Fonts/Supplemental/Arial.ttf"
B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FON, KUTU, KOYU, ORTA, VURGU = "#F3EEE4", "#E6E4DF", "#2B2B2B", "#8A8782", "#C4532D"

SIPARIS = 393
SATIRLAR = (("S100001", "İzmir", "Karşıyaka", "Çelik Termos 750 ml", "459,90 TL"),
            ("S100002", "İstanbul", "Beşiktaş", "Çelik Termos 750 ml", "459,90 TL"),
            ("S100003", "Ankara", "Mamak", "Çelik Termos 500 ml", "779,80 TL"),
            ("S100004", "Malatya", "Battalgazi", "Çelik Termos 750 ml", "459,90 TL"),
            ("S100006", "İzmir", "Bornova", "Termos Kupa 350 ml", "279,90 TL"),
            ("S100007", "İzmir", "Buca", "Çelik Termos 500 ml", "1.169,70 TL"),
            ("S100008", "Ankara", "Mamak", "Çelik Termos 500 ml", "389,90 TL"))
# (il, sipariş, pay, (ilçe, sipariş) × 3)
ILLER = (("İstanbul", 118, "%30,0", (("Ümraniye", 33), ("Bağcılar", 20), ("Esenyurt", 19))),
         ("Ankara", 65, "%16,5", (("Yenimahalle", 20), ("Mamak", 17), ("Çankaya", 16))),
         ("İzmir", 44, "%11,2", (("Karşıyaka", 15), ("Konak", 11), ("Bornova", 9))))
# Aracın örnek dosyadaki ilk önerisinin kısaltılmışı (agent.py analiz ornek/ornek_siparisler.csv, 1. madde)
ONERI = ("İlk üç ilin payı %57,8.", "Reklam bütçesinin ana bölümünü bu üç ile ayırın.")
KOLON = (96, 262, 432, 610, 990)      # sipariş no, il, ilçe, ürün, tutar (sağa yaslı)
X0, OLCEK = 270, 500 / 118            # çubukların başlangıcı ve sipariş başına genişlik
BLOK_Y, BLOK = 566, 158
Z = {"oku": (0.03, 0.28), "hat": (0.28, 0.33), "blok": (0.34, 0.86), "alt": (0.87, 0.95)}
KARE, SURE, BEKLE = 90, 70, 3000


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
def numara(d, x, y, no):
    d.ellipse(k(x - 17, y - 17, x + 17, y + 17), fill=VURGU); yaz(d, x, y - 12, str(no), 20, FON, True, "orta")


# ---- değişmeyen zemin
taban = Image.new("RGB", (EN * K, BOY * K), FON)
d = ImageDraw.Draw(taban)
yaz(d, 60, 50, "SATIŞ BÖLGE ANALİZCİSİ", 16, ORTA, True)
yaz(d, 60, 80, "Sipariş listenizi verin,", 50, KOYU, True)
yaz(d, 60, 138, "analizi ve önerileri alın.", 50, VURGU, True)
d.rounded_rectangle(k(60, 212, 1020, 470), radius=20 * K, fill=KUTU)
numara(d, 100, 248, 1); yaz(d, 130, 233, "Sipariş listeniz", 25, KOYU, True)
d.rounded_rectangle(k(246, 276, 596, 428), radius=12 * K, fill=FON)     # okunan iki sütun
for x, ad in zip(KOLON, ("Sipariş no", "İl", "İlçe", "Ürün", "Tutar")):
    yaz(d, x, 284, ad, 16, KOYU if ad in ("İl", "İlçe") else ORTA, True, "sag" if ad == "Tutar" else "sol")
yaz(d, 96, 438, "Araç yalnızca il ve ilçeyi sayar; müşteri adı, telefon ve adres gerekmez.", 17, ORTA)
numara(d, 100, 536, 2); yaz(d, 130, 521, "İl ve ilçe dağılımı", 25, KOYU, True)
yaz(d, 1020, 527, "sipariş sayısı", 17, ORTA, hiza="sag")
d.rounded_rectangle(k(60, 1052, 1020, 1146), radius=20 * K, fill=KUTU)
yaz(d, 60, 1168, "Rapor sayfası ve Excel: iller, ilçeler, mahalleler, iade, bulgular ve öneriler.", 17, ORTA)
yaz(d, 60, 1266, "Harun Gökce  ·  github.com/Harungokc/eticaret-agentlari", 18, ORTA)
yaz(d, 1020, 1267, "Örnek veri: 400 uydurma sipariş", 16, ORTA, hiza="sag")


def kare_ciz(t):
    c = taban.copy(); cd = ImageDraw.Draw(c)

    # 1: satırlar akar, sipariş sayısı artar
    op = oran(t, *Z["oku"])
    w = yaz(cd, 990, 236, " sipariş okundu", 20, ORTA, hiza="sag")
    yaz(cd, 990 - w, 233, str(round(SIPARIS * yumusak(op))), 24, VURGU if 0 < op < 1 else KOYU, True, "sag")
    kay = min(len(SATIRLAR) - 4, int(op * 14) % (len(SATIRLAR) - 3)) if op < 1 else len(SATIRLAR) - 4
    for j, satir in enumerate(SATIRLAR[kay:kay + 4]):
        y = 314 + j * 28
        for x, hucre, ad in zip(KOLON, satir, "nilut"):
            onemli = ad in "il"
            yaz(cd, x, y, hucre, 18, KOYU if onemli else ORTA, onemli, "sag" if ad == "t" else "sol")

    # 1 → 2 bağlantısı
    hp = yumusak(oran(t, *Z["hat"]))
    if hp > 0:
        cd.line(k(540, 470, 540, 470 + 30 * hp), fill=VURGU, width=5 * K)
        cd.ellipse(k(531, 461 + 30 * hp, 549, 479 + 30 * hp), fill=VURGU, outline=FON, width=2 * K)

    # 2: iller sırayla açılır; her ilin altında ilçeleri
    bp = oran(t, *Z["blok"])
    for j, (il, adet, pay, ilceler) in enumerate(ILLER):
        yerel = oran(bp, j / len(ILLER), (j + 1) / len(ILLER))
        y = BLOK_Y + j * BLOK
        g = yumusak(oran(yerel, 0, 0.12))
        yaz(cd, 60, y, il, 27, karis(KOYU, FON, 0.2 + 0.8 * g), True)
        p = yumusak(oran(yerel, 0.05, 0.40))
        if p > 0:
            cd.rounded_rectangle(k(X0, y + 4, X0 + adet * OLCEK * p, y + 28), radius=6 * K, fill=KOYU)
        if p >= 1:
            w = yaz(cd, X0 + adet * OLCEK + 14, y + 2, str(adet), 23, KOYU, True)
            yaz(cd, X0 + adet * OLCEK + 22 + w, y + 5, f"sipariş  ·  payı {pay}", 19, ORTA)
        for i, (ilce, n) in enumerate(ilceler):
            yy = y + 46 + i * 32
            q = yumusak(oran(yerel, 0.42 + i * 0.16, 0.62 + i * 0.16))
            yaz(cd, 84, yy, ilce, 20, karis(ORTA, FON, 0.25 + 0.75 * yumusak(oran(q, 0, 0.3))))
            if q > 0:
                cd.rounded_rectangle(k(X0, yy + 4, X0 + max(n * OLCEK * q, 8), yy + 20), radius=5 * K, fill=VURGU)
            if q >= 1:
                yaz(cd, X0 + n * OLCEK + 12, yy, str(n), 20, VURGU, True)

    # alt kutu: aracın önerisi
    ap = yumusak(oran(t, *Z["alt"]))
    yaz(cd, 84, 1066, "ÖNERİ", 18, karis(VURGU, KUTU, ap), True)
    w = yaz(cd, 84, 1100, ONERI[0] + " ", 23, karis(KOYU, KUTU, ap), True)
    yaz(cd, 84 + w, 1100, ONERI[1], 23, karis(KOYU, KUTU, ap))
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
kareler[int(KARE * 0.55)].save(sys.argv[1].replace(".gif", "-ara.png"))
print("kare:", KARE, "süre (sn):", round((SURE * (KARE - 1) + BEKLE) / 1000, 1))
