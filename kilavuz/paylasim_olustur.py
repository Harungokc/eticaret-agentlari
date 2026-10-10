"""LinkedIn paylaşımı için kaydırmalı belge (carousel) üretir: 1080×1350 sayfalı bir PDF.

Çalıştırmak için (reportlab gerekir): python kilavuz/paylasim_olustur.py [çıktı.pdf]
PDF, LinkedIn'e "belge" olarak yüklenir; her sayfa bir kaydırma adımı olur.
"""

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

EN, BOY = 1080, 1350
KENAR = 90
GELISTIREN, EPOSTA = "Harun Gökce", "harungokce70@gmail.com"
ADRES = "github.com/Harungokc/eticaret-agentlari"

YAZI_TIPLERI = {
    "Govde": ["/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arial.ttf"],
    "Kalin": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"],
}
for ad, yollar in YAZI_TIPLERI.items():
    yol = next((y for y in yollar if Path(y).exists()), None)
    if yol is None:
        raise SystemExit(f"Yazı tipi bulunamadı: {ad}")
    pdfmetrics.registerFont(TTFont(ad, yol))
pdfmetrics.registerFontFamily("Govde", normal="Govde", bold="Kalin", italic="Govde", boldItalic="Kalin")

LACIVERT, SARI, GRI, ACIK, CIZGI, KIRMIZI, YESIL, TURUNCU = (colors.HexColor(r) for r in
                                                             ("#1F3864", "#FFC83D", "#5B6675", "#F3F6FB", "#D9DFE8", "#C0392B", "#1E8E5A", "#C77700"))
ZORLUK_RENGI = {"Kolay": YESIL, "Orta": TURUNCU, "Zor": KIRMIZI}


def bicem(boyut, renk=colors.black, kalin=False, satir=None, hiza=0):
    return ParagraphStyle("b", fontName="Kalin" if kalin else "Govde", fontSize=boyut, leading=satir or boyut * 1.28,
                          textColor=renk, alignment=hiza)


def yaz(c, metin, x, y, genislik, stil):
    """Metni (x, y) üst sol köşesinden başlatarak yazar; kapladığı yüksekliği döndürür."""
    p = Paragraph(metin, stil)
    _, h = p.wrap(genislik, BOY)
    p.drawOn(c, x, y - h)
    return h


def zemin(c, renk):
    c.setFillColor(renk)
    c.rect(0, 0, EN, BOY, stroke=0, fill=1)


def alt_bilgi(c, no, toplam, koyu=False):
    renk = colors.HexColor("#C9D6F2") if koyu else GRI
    c.setFillColor(renk)
    c.setFont("Govde", 24)
    c.drawString(KENAR, 62, f"{GELISTIREN}  ·  {ADRES}")
    c.drawRightString(EN - KENAR, 62, f"{no} / {toplam}")
    if no < toplam:
        c.setFont("Kalin", 30)
        c.drawRightString(EN - KENAR, 110, "Kaydırın  →")


def ust_serit(c, etiket):
    c.setFillColor(LACIVERT)
    c.rect(0, BOY - 26, EN, 26, stroke=0, fill=1)
    c.setFillColor(SARI)
    c.rect(KENAR, BOY - 150, 70, 10, stroke=0, fill=1)
    c.setFillColor(GRI)
    c.setFont("Kalin", 26)
    c.drawString(KENAR, BOY - 118, etiket)


def kart(c, y, yukseklik, renk=ACIK):
    c.setFillColor(renk)
    c.setStrokeColor(CIZGI)
    c.roundRect(KENAR, y - yukseklik, EN - 2 * KENAR, yukseklik, 18, stroke=1, fill=1)


def kapak(c, no, toplam):
    zemin(c, LACIVERT)
    c.setFillColor(SARI)
    c.rect(KENAR, BOY - 250, 110, 14, stroke=0, fill=1)
    y = BOY - 300
    y -= yaz(c, "80 açık kaynak yapay zekâ aracına tek tek baktım.", KENAR, y, EN - 2 * KENAR, bicem(84, colors.white, True, 98))
    y -= 50
    y -= yaz(c, "Bir e-ticaret satıcısı hangisini gerçekten kullanabilir?", KENAR, y, EN - 2 * KENAR, bicem(56, SARI, True, 70))
    y -= 60
    yaz(c, "Trendyol, Hepsiburada ve n11 satıcıları için bir rehber", KENAR, y, EN - 2 * KENAR, bicem(36, colors.HexColor("#C9D6F2"), False, 48))
    alt_bilgi(c, no, toplam, koyu=True)


def bulgu(sira, baslik, giris, satirlar, sonuc):
    def ciz(c, no, toplam):
        zemin(c, colors.white)
        ust_serit(c, f"BULGU {sira} / 3")
        y = BOY - 190
        y -= yaz(c, baslik, KENAR, y, EN - 2 * KENAR, bicem(62, LACIVERT, True, 74))
        y -= 34
        y -= yaz(c, giris, KENAR, y, EN - 2 * KENAR, bicem(34, GRI, False, 46))
        y -= 44
        for ad, deger, not_ in satirlar:
            kart(c, y, 150)
            yaz(c, ad, KENAR + 34, y - 28, 420, bicem(36, colors.black, True))
            yaz(c, deger, KENAR + 34, y - 84, 420, bicem(28, GRI))
            yaz(c, not_, KENAR + 480, y - 34, EN - 2 * KENAR - 514, bicem(30, KIRMIZI, True, 38))
            y -= 174
        y -= 20
        yaz(c, sonuc, KENAR, y, EN - 2 * KENAR, bicem(36, colors.black, True, 48))
        alt_bilgi(c, no, toplam)
    return ciz


def tablo_sayfasi(etiket, baslik, giris, satirlar, sonuc=""):
    def ciz(c, no, toplam):
        zemin(c, colors.white)
        ust_serit(c, etiket)
        y = BOY - 190
        y -= yaz(c, baslik, KENAR, y, EN - 2 * KENAR, bicem(58, LACIVERT, True, 70))
        y -= 26
        if giris:
            y -= yaz(c, giris, KENAR, y, EN - 2 * KENAR, bicem(32, GRI, False, 43))
            y -= 34
        for sol, sag, zorluk in satirlar:
            genislik = 560 if zorluk else EN - 2 * KENAR - 60
            kart(c, y, 110)
            yaz(c, sol, KENAR + 30, y - 20, genislik, bicem(31, colors.black, True, 38))
            yaz(c, sag, KENAR + 30, y - 66, genislik, bicem(26, GRI))
            if zorluk:
                yaz(c, zorluk, KENAR + 610, y - 38, EN - 2 * KENAR - 640, bicem(28, ZORLUK_RENGI.get(zorluk, GRI), True, 34, hiza=2))
            y -= 124
        if sonuc:
            yaz(c, sonuc, KENAR, y - 30, EN - 2 * KENAR, bicem(34, colors.black, True, 46))
        alt_bilgi(c, no, toplam)
    return ciz


def eksikler(c, no, toplam):
    zemin(c, colors.white)
    ust_serit(c, "TÜRKİYE'DE EKSİK OLANLAR")
    y = BOY - 190
    y -= yaz(c, "Satıcının işine yarayacak ama henüz kimsenin yapmadığı altı şey", KENAR, y, EN - 2 * KENAR, bicem(54, LACIVERT, True, 66))
    y -= 44
    maddeler = [
        "Pazaryeri dökümlerinden <b>gerçek kâr</b>: hakediş, komisyon, kargo, iade, reklam",
        "Türkiye pazaryeri kurallarını bilen <b>ilan denetçisi</b>",
        "Müşteri sorusuna <b>cevap taslağı</b>; göndermeyi satıcı onaylar",
        "Çok pazaryerli <b>stok özeti</b>: “şu ürün bitiyor”",
        "Pazaryeri <b>reklam raporu</b> analizi",
        "<b>Trendyol dışındaki</b> pazaryerleri için araçlar",
    ]
    for i, m in enumerate(maddeler, 1):
        c.setFillColor(LACIVERT if i == 1 else ACIK)
        c.setStrokeColor(CIZGI)
        c.circle(KENAR + 34, y - 34, 34, stroke=1, fill=1)
        c.setFillColor(colors.white if i == 1 else LACIVERT)
        c.setFont("Kalin", 34)
        c.drawCentredString(KENAR + 34, y - 46, str(i))
        h = yaz(c, m, KENAR + 100, y - 8, EN - 2 * KENAR - 100, bicem(34, colors.black, False, 44))
        y -= max(h, 68) + 34
    yaz(c, "Birincisi dört ayrı incelemenin dördünde de eksik çıktı. Sıradaki araç o.", KENAR, y - 6, EN - 2 * KENAR, bicem(32, GRI, False, 43))
    alt_bilgi(c, no, toplam)


def cagri(c, no, toplam):
    zemin(c, LACIVERT)
    c.setFillColor(SARI)
    c.rect(KENAR, BOY - 250, 110, 14, stroke=0, fill=1)
    y = BOY - 300
    y -= yaz(c, "Sıradaki araç: pazaryeri dökümünden gerçek kâr.", KENAR, y, EN - 2 * KENAR, bicem(66, colors.white, True, 80))
    y -= 50
    y -= yaz(c, "Bunun için gerçek bir hakediş ya da sipariş dökümü görmem gerekiyor. Müşteri bilgilerini silip "
                "paylaşabilecek olan varsa yazsın; aracı o dosyayla çalışacak şekilde yazarım.",
             KENAR, y, EN - 2 * KENAR, bicem(38, colors.HexColor("#E3EAF7"), False, 52))
    y -= 70
    c.setFillColor(colors.white)
    c.roundRect(KENAR, y - 230, EN - 2 * KENAR, 230, 20, stroke=0, fill=1)
    yaz(c, "Rehberin tamamı", KENAR + 40, y - 36, EN - 2 * KENAR - 80, bicem(30, GRI))
    yaz(c, ADRES, KENAR + 40, y - 86, EN - 2 * KENAR - 80, bicem(38, LACIVERT, True))
    yaz(c, f"{GELISTIREN}  ·  {EPOSTA}", KENAR + 40, y - 156, EN - 2 * KENAR - 80, bicem(30, colors.black))
    alt_bilgi(c, no, toplam, koyu=True)


SAYFALAR = [
    kapak,
    bulgu(1, "En popüler araçların çoğunu bir satıcı kendi kuramıyor",
          "Çoğu, sunucuya kurulan büyük yazılımlar.",
          [("Metabase", "Satış panosu · 50 bin yıldız", "Sunucu ve veritabanı ister"),
           ("ERPNext", "Stok ve sipariş · 40 bin yıldız", "Sunucu ister"),
           ("Chatwoot", "Müşteri mesajları · 38 bin yıldız", "Sunucu ister; yapay zekâ ajanı ücretli bölümde")],
          "Kod bilmeden kurulabilenler az: masaüstü uygulamaları ve Claude'a yüklenen hazır beceriler."),
    bulgu(2, "“Açık kaynak” yazanların bir kısmı değil",
          "Yıldız sayısı yüksek diye lisansı temiz olmuyor.",
          [("n8n", "Otomasyon · 207 bin yıldız", "Lisansı ticari dağıtımı kısıtlıyor"),
           ("Bir reklam deposu", "4,4 bin yıldız", "Depoda kaynak kod dosyası yok"),
           ("Bir Meta reklam aracı", "1,3 bin yıldız", "Lisansı Business Source License; açık kaynak değil")],
          "Kullanmadan önce üç şeye bakın: lisans dosyası, son güncelleme, depoda gerçekten kod var mı."),
    bulgu(3, "Türkiye pazaryerleri için kullanılan bir araç neredeyse yok",
          "Satıcıya özel araçların hemen hepsi Amazon'a göre yazılmış.",
          [("Trendyol", "Bulunan bağlantı depoları", "En çok yıldızlısı 8 yıldız"),
           ("Hepsiburada, n11", "Yapay zekâ aracı ya da beceri", "Bulunamadı"),
           ("Çiçeksepeti, Pazarama", "Yapay zekâ aracı ya da beceri", "Bulunamadı")],
          "Kimse öne geçmiş değil. Alan yeni kalabalıklaşıyor."),
    tablo_sayfasi("KULLANILABİLENLER", "Bir satıcının bugün kullanabileceği araçlar", "Lisansı temiz ve güncel. Sağda: kurulum zorluğu.",
                  [("İlan ve satış metni", "marketingskills · 54 bin yıldız · MIT", "Kolay"),
                   ("Ürün fotoğrafını netleştirme", "Upscayl · 50 bin yıldız · masaüstü", "Kolay"),
                   ("Excel, PDF, sunum", "anthropics/skills · Claude'da hazır", "Kolay"),
                   ("Reklam denetimi", "claude-ads · 10 bin yıldız · MIT", "Orta"),
                   ("İş akışı otomasyonu", "Activepieces · 25 bin yıldız", "Orta"),
                   ("Arka plan silme", "rembg · 25 bin yıldız · MIT", "Zor")]),
    tablo_sayfasi("TÜRKİYE İÇİN", "Boş kalan yer için dört küçük araç yazdım",
                  "Claude'a ya da ChatGPT'ye tek dosya yüklenir. Ücretsiz, açık kaynak, kurulum yok.",
                  [("Hangi pazaryerinde elime ne kalır?", "Kategori ve fiyat yeterli", ""),
                   ("Fiyatım pazarda nerede duruyor?", "Ürün listesinden konum ve rakip karşılaştırması", ""),
                   ("Müşteriler neden şikâyet ediyor?", "Yorumlardan şikâyet ve talep çıkarır", ""),
                   ("Satışlarım hangi illere gidiyor?", "Sipariş listesinden il ve bölge dağılımı", "")],
                  sonuc="Her rakam koddan gelir; asistan rakam uydurmaz. Araçlar pazaryerinden veri çekmez, veriyi siz verirsiniz."),
    eksikler,
    cagri,
]


def main() -> None:
    hedef = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "Rehber-LinkedIn.pdf"
    c = canvas.Canvas(str(hedef), pagesize=(EN, BOY))
    c.setTitle("E-ticaret Satıcısı için Yapay Zekâ Araçları Rehberi")
    c.setAuthor(GELISTIREN)
    for no, sayfa in enumerate(SAYFALAR, 1):
        sayfa(c, no, len(SAYFALAR))
        c.showPage()
    c.save()
    print(hedef)


if __name__ == "__main__":
    main()
