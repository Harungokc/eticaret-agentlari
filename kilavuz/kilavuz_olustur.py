"""Kullanım kılavuzunu (PDF) üretir.

    pip install reportlab
    python kilavuz/kilavuz_olustur.py

Yalnızca kılavuzu yeniden üretmek için gerekir; aracın kendisi ek paket kullanmaz.
"""

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import CondPageBreak, Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

DEPO = "https://github.com/Harungokc/eticaret-agentlari"
ZIP = DEPO + "/archive/refs/heads/main.zip"
CIKTI = Path(__file__).parent / "Pazar-ve-Komisyon-Analizcisi-Kilavuz.pdf"
GORSELLER = Path(__file__).parent / "gorseller"
GELISTIREN = "Harun Gökce"
EPOSTA = "harungokce70@gmail.com"
TELEFON = "0506 155 46 42"

# Türkçe harfler için sistem yazı tipleri (macOS ve Windows yolları)
YAZI_TIPLERI = {
    "Govde": ["/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arial.ttf"],
    "Govde-Kalin": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"],
    "Kod": ["/System/Library/Fonts/Supplemental/Courier New.ttf", "C:/Windows/Fonts/cour.ttf"],
    "Kod-Kalin": ["/System/Library/Fonts/Supplemental/Courier New Bold.ttf", "C:/Windows/Fonts/courbd.ttf"],
}
for ad, yollar in YAZI_TIPLERI.items():
    yol = next((y for y in yollar if Path(y).exists()), None)
    if yol is None:
        raise SystemExit(f"Yazı tipi bulunamadı: {ad}")
    pdfmetrics.registerFont(TTFont(ad, yol))
pdfmetrics.registerFontFamily("Govde", normal="Govde", bold="Govde-Kalin", italic="Govde", boldItalic="Govde-Kalin")

LACIVERT, MAVI, ACIK, SARI, GRI, CIZGI = (colors.HexColor(r) for r in ("#1F3864", "#1F4FD8", "#EEF4FF", "#FFF7CC", "#5B6675", "#DFE3E8"))

S = {
    "kapak": ParagraphStyle("kapak", fontName="Govde-Kalin", fontSize=26, leading=31, textColor=LACIVERT, spaceAfter=6),
    "kapak_alt": ParagraphStyle("kapak_alt", fontName="Govde", fontSize=13, leading=18, textColor=GRI, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="Govde-Kalin", fontSize=16, leading=20, textColor=LACIVERT, spaceBefore=18, spaceAfter=8,
                         keepWithNext=True),
    "h2": ParagraphStyle("h2", fontName="Govde-Kalin", fontSize=12, leading=16, textColor=LACIVERT, spaceBefore=10, spaceAfter=4,
                         keepWithNext=True),
    "p": ParagraphStyle("p", fontName="Govde", fontSize=10.5, leading=15, spaceAfter=6),
    "kucuk": ParagraphStyle("kucuk", fontName="Govde", fontSize=9, leading=12.5, textColor=GRI, spaceAfter=4),
    "madde": ParagraphStyle("madde", fontName="Govde", fontSize=10.5, leading=15, leftIndent=16, bulletIndent=4, spaceAfter=3),
    "adim": ParagraphStyle("adim", fontName="Govde", fontSize=10.5, leading=15, leftIndent=22, bulletIndent=2, spaceAfter=5),
    "kutu": ParagraphStyle("kutu", fontName="Govde", fontSize=10.5, leading=15),
    "kod": ParagraphStyle("kod", fontName="Kod", fontSize=8.6, leading=11.5),
    "hucre": ParagraphStyle("hucre", fontName="Govde", fontSize=9.5, leading=13),
    "hucre_b": ParagraphStyle("hucre_b", fontName="Govde-Kalin", fontSize=9.5, leading=13, textColor=colors.white),
    "orta": ParagraphStyle("orta", fontName="Govde", fontSize=9, leading=12, textColor=GRI, alignment=TA_CENTER),
}
GENISLIK = A4[0] - 40 * mm


def p(metin, bicem="p"):
    return Paragraph(metin, S[bicem])


def maddeler(ogeler, numarali=False):
    return [Paragraph(m, S["adim" if numarali else "madde"], bulletText=f"{i}." if numarali else "•") for i, m in enumerate(ogeler, 1)]


def kutu(metin, renk=ACIK, baslik=None):
    icerik = ([Paragraph(f"<b>{baslik}</b>", S["kutu"]), Spacer(1, 3)] if baslik else []) + [Paragraph(metin, S["kutu"])]
    t = Table([[icerik]], colWidths=[GENISLIK])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), renk), ("BOX", (0, 0), (-1, -1), 0.5, CIZGI),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return KeepTogether([t, Spacer(1, 8)])


def kod(metin):
    t = Table([[Preformatted(metin.strip("\n"), S["kod"])]], colWidths=[GENISLIK])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F5F7")), ("BOX", (0, 0), (-1, -1), 0.5, CIZGI),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return KeepTogether([t, Spacer(1, 8)])


def tablo(basliklar, satirlar, genislikler):
    veri = [[Paragraph(b, S["hucre_b"]) for b in basliklar]] + [[Paragraph(h, S["hucre"]) for h in s] for s in satirlar]
    t = Table(veri, colWidths=[GENISLIK * g for g in genislikler], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), LACIVERT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LINEBELOW", (0, 0), (-1, -1), 0.5, CIZGI), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFBFC")]),
                           ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return [t, Spacer(1, 10)]


def gelistiren_kutusu():
    """Kapakta, başlığın hemen altında duran geliştirici bandı."""
    sol = Paragraph("<font color='#C9D6F2' size='8.5'>GELİŞTİREN</font><br/><font size='13'><b>" + GELISTIREN + "</b></font>",
                    ParagraphStyle("g1", fontName="Govde", fontSize=13, leading=17, textColor=colors.white))
    sag = Paragraph(f"<font color='#C9D6F2' size='8.5'>İLETİŞİM</font><br/>{EPOSTA} &nbsp;·&nbsp; {TELEFON}",
                    ParagraphStyle("g2", fontName="Govde", fontSize=10.5, leading=17, textColor=colors.white))
    t = Table([[sol, sag]], colWidths=[GENISLIK * 0.38, GENISLIK * 0.62])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LACIVERT), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    return [t, Spacer(1, 12)]


def gorsel(dosya, aciklama):
    yol = GORSELLER / dosya
    r = Image(str(yol))
    oran = r.imageHeight / r.imageWidth
    en = GENISLIK * 0.80
    r.drawWidth, r.drawHeight = en, en * oran
    cerceve = Table([[r]], colWidths=[en], hAlign="CENTER")
    cerceve.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, CIZGI), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return KeepTogether([cerceve, Spacer(1, 3), Paragraph(aciklama, S["orta"]), Spacer(1, 10)])


def alt_bilgi(tuval, belge):
    tuval.saveState()
    tuval.setFont("Govde", 8.5)
    tuval.setFillColor(GRI)
    tuval.drawString(20 * mm, 11 * mm, f"Pazar ve Komisyon Analizcisi — Geliştiren: {GELISTIREN} · {EPOSTA}")
    tuval.drawRightString(A4[0] - 20 * mm, 11 * mm, f"Sayfa {belge.page}")
    tuval.restoreState()


def icerik():
    h = []

    # ------------------------------------------------------------ kapak ve özet
    h += [Spacer(1, 6), p("Pazar ve Komisyon Analizcisi", "kapak"),
          p("Yapay zekâ asistanınızla kurulum ve kullanım kılavuzu", "kapak_alt")]
    h += gelistiren_kutusu()
    h.append(kutu(
        "Bu kılavuzu, bilgisayarınızda komut çalıştırabilen bir yapay zekâ asistanına verin ve "
        "<b>“Bu kılavuzdaki aracı kur.”</b> deyin. Asistan aracı kendisi indirir, kurar ve dener; sizin başka bir "
        "dosya ya da adres vermeniz gerekmez. Sonrasında ona "
        "konuşur gibi yazarsınız: <i>“899 liralık kadın ayakkabıyı hangi pazaryerinde satmalıyım?”</i> "
        "Asistan hesabı araçla yapar, sonucu size anlatır ve isterseniz Google Sheets tablonuza yazar.",
        baslik="Bu kılavuz nasıl kullanılır"))

    h.append(p("Araç ne yapar", "h2"))
    h += maddeler([
        "<b>Komisyon karşılaştırması:</b> Kategori ve satış fiyatına göre Trendyol, Hepsiburada, n11 ve Amazon Türkiye'nin "
        "keseceği komisyonu, elinize geçecek tutarı ve kârınızı yan yana gösterir.",
        "<b>Pazar analizi:</b> Bir ürün listesinden fiyat bantlarını, öne çıkan markaları, rekabet yoğunluğunu ve az rakipli "
        "fiyat aralığını çıkarır.",
        "<b>Google Sheets ve Excel çıktısı:</b> Sonuçları tablonuza yazar ve Google Sheets'te grafiklerle destekler. Tablodaki "
        "sarı hücreleri (fiyat, maliyet, oranlar) değiştirdiğinizde sonuçlar ve grafikler kendiliğinden güncellenir.",
    ])

    h.append(p("Örnek bir konuşma", "h2"))
    h += tablo(["Siz", "Asistan"], [
        ["899 liralık kadın ayakkabı satacağım, maliyetim 400 lira. Hangi pazaryeri daha kârlı? Sonucu tabloma da yaz.",
         "Hesabı yaptım. Hepsiburada'da elinize 724–737 TL, n11'de 698–746 TL, Trendyol'da 697–706 TL geçiyor. Ortalamada "
         "Hepsiburada önde, ama n11'in oran aralığı onunla çakışıyor; kesin sıralama için sözleşmenizdeki oranları söylerseniz "
         "yeniden hesaplarım. Kargo ve diğer kesintiler bu hesaba dahil değil. Sonucu tablonuzun Komisyon sekmesine yazdım."],
    ], [0.38, 0.62])

    h.append(p("Gerekenler", "h2"))
    h += maddeler([
        "Windows, macOS veya Linux bir bilgisayar",
        "Python 3.10 veya üstü (yoksa asistanınız kurmanızı ister; python.org/downloads adresinden ücretsiz indirilir)",
        "Google Sheets çıktısı için bir Google hesabı (isteğe bağlı; bu özellik olmadan da araç çalışır)",
    ])

    h.append(PageBreak())
    h.append(p("Sonuç tablonuzda böyle görünür", "h2"))
    h.append(p("Aşağıdaki görüntüler aracın Google Sheets'e yazdığı gerçek sayfalardır. İçlerindeki ürün ve markalar örnek "
               "amaçlı uydurma verilerdir."))
    h.append(gorsel("google-sheets-komisyon.png", "Komisyon sekmesi: sarı hücreleri değiştirdiğinizde tablo ve grafikler güncellenir."))
    h.append(gorsel("google-sheets-pazar.png", "Pazar sekmesi: fiyat özeti, fiyat bantları, öne çıkan markalar ve grafikler."))


    h.append(CondPageBreak(75 * mm))
    h.append(p("Hangi asistanla çalışır", "h2"))
    h.append(p("Asistanın iki şeyi yapabilmesi gerekir: <b>bilgisayarınızda komut çalıştırmak</b> ve <b>internete çıkmak</b> "
               "(aracı GitHub'dan indirmek ve tablonuza yazmak için Google'a bağlanmak)."))
    h += tablo(["Asistan türü", "Uygun mu"], [
        ["Bilgisayarınızda çalışan ajan asistanlar (ör. Claude Code, Claude Cowork; OpenAI tarafında Codex gibi araçlar)",
         "Evet. Bu kılavuz onlar için yazıldı."],
        ["Yalnızca sohbet penceresi (tarayıcıdaki claude.ai veya ChatGPT sohbeti)",
         "Kurulumu yapamaz, çünkü bilgisayarınızda komut çalıştıramaz ve internetten program indiremez. Bu durumda "
         "aracı kendiniz kurabilirsiniz; adımlar proje sayfasında yazılıdır."],
    ], [0.55, 0.45])
    h.append(p("Komutlar Claude Code ile macOS üzerinde denenmiştir. Asistanın indirdiği programı çalıştırabilmesi sizin "
               "onayınıza bağlıdır; tam otomatik çalışan ayarlarda asistan bu adımı reddedebilir (bkz. Bölüm B).", "kucuk"))


    # ------------------------------------------------------------ bölüm A
    h.append(p("Bölüm A — Sizin yapacağınız iş: Google Sheets bağlantısı", "h1"))
    h.append(p("Bu bölümü asistan sizin yerinize yapamaz, çünkü Google hesabınıza giriş gerektirir. Bir kez yapılır ve "
               "yaklaşık 10 dakika sürer. Sonuçları yalnızca Excel olarak almak istiyorsanız bu bölümü atlayabilirsiniz."))
    h.append(kutu("Aracın tablonuza yazabilmesi için ona ait bir “robot hesap” (hizmet hesabı) oluşturur, bu hesabın anahtar "
                  "dosyasını indirir ve tablonuzu o hesapla paylaşırsınız. Araç yalnızca paylaştığınız tabloya erişebilir.",
                  baslik="Ne yapıyoruz"))

    h.append(p("1. Proje oluşturun", "h2"))
    h += maddeler([
        "Tarayıcınızda <b>console.cloud.google.com</b> adresini açın ve Google hesabınızla giriş yapın.",
        "Sayfanın üstündeki proje seçicisine tıklayın ve <b>New Project</b> (Yeni proje) deyin.",
        "Bir ad verin (örneğin “E-ticaret”) ve <b>Create</b> (Oluştur) düğmesine basın. Proje seçili hâle gelsin.",
    ], numarali=True)

    h.append(p("2. Google Sheets API'yi açın", "h2"))
    h += maddeler([
        "Üstteki arama kutusuna <b>Google Sheets API</b> yazın ve çıkan sonuca tıklayın.",
        "<b>Enable</b> (Etkinleştir) düğmesine basın.",
    ], numarali=True)

    h.append(p("3. Hizmet hesabını oluşturun", "h2"))
    h += maddeler([
        "Sol üstteki menüden <b>IAM &amp; Admin → Service Accounts</b> (IAM ve Yönetici → Hizmet Hesapları) sayfasına gidin.",
        "<b>+ Create service account</b> düğmesine basın.",
        "Bir ad yazın (örneğin “tablo-yazici”) ve <b>Create and continue</b> deyin.",
        "Rol seçme adımını boş bırakıp <b>Done</b> (Bitti) düğmesine basın. Rol vermenize gerek yoktur.",
    ], numarali=True)

    h.append(p("4. Anahtar dosyasını indirin", "h2"))
    h += maddeler([
        "Listede yeni oluşan hesabın adına tıklayın.",
        "Üstteki <b>Keys</b> (Anahtarlar) sekmesine geçin.",
        "<b>Add key → Create new key</b> deyin, <b>JSON</b> seçili kalsın ve <b>Create</b> düğmesine basın.",
        "Bilgisayarınıza <b>.json</b> uzantılı bir dosya iner. Nereye indiğini not edin (genellikle İndirilenler klasörü).",
    ], numarali=True)
    h.append(kutu("Bu dosya tablonuza erişim şifresi gibidir. Kimseyle paylaşmayın, sohbete içeriğini yapıştırmayın ve "
                  "e-postayla göndermeyin. Asistanınıza yalnızca dosyanın bilgisayarınızdaki <b>yerini</b> söyleyeceksiniz.",
                  renk=SARI, baslik="Anahtar dosyasını koruyun"))

    h.append(p("5. Tablonuzu hizmet hesabıyla paylaşın", "h2"))
    h += maddeler([
        "Service Accounts sayfasında hesabın <b>e-posta adresini</b> kopyalayın. Adres şuna benzer: "
        "<font face='Kod' size='9'>tablo-yazici@proje-adi.iam.gserviceaccount.com</font>",
        "Sonuçların yazılmasını istediğiniz Google Sheets tablosunu açın (yoksa sheets.new adresinden boş bir tablo oluşturun).",
        "Sağ üstteki <b>Paylaş</b> düğmesine basın, kopyaladığınız adresi yapıştırın ve yetkiyi <b>Düzenleyen</b> yapın.",
        "“Kişilere bildirim gönder” kutusunun işaretini kaldırıp <b>Paylaş</b> düğmesine basın.",
        "Tablonun tarayıcıdaki adresini kopyalayın; asistanınıza vereceksiniz.",
    ], numarali=True)
    h.append(p("Bu bölümün sonunda elinizde iki şey olmalı: <b>tablonuzun adresi</b> ve <b>anahtar dosyasının bilgisayarınızdaki yeri</b>."))

    # ------------------------------------------------------------ bölüm B
    h.append(p("Bölüm B — Asistanınıza vereceğiniz ilk mesaj", "h1"))
    h.append(p("Bu PDF'i asistanınıza ekleyin ve aşağıdaki mesajı, köşeli parantezli yerleri doldurarak gönderin."))
    h.append(kod("""
Ekteki kılavuzda anlatılan aracı bilgisayarıma kur, testlerini çalıştır
ve örnek bir komisyon hesabıyla çalıştığını göster.

Google Sheets bağlantımı da kur:
- Tablo adresim: [tablonuzun adresi]
- Anahtar dosyam: [anahtar dosyasının yeri, ör. ~/Downloads/proje-abc123.json]

Anahtar dosyasının içeriğini ekrana yazma.
"""))
    h.append(p("Google Sheets kullanmayacaksanız mesajın ikinci paragrafını silin."))
    h.append(kutu("Asistanınız internetten indirdiği bir programı çalıştırmadan ya da tablonuza yazmadan önce sizden <b>izin "
                  "ister</b>; bazı ayarlarda ise bu adımı kendiliğinden <b>reddeder</b> ve “indirilen programı çalıştıramıyorum” "
                  "der. Bu bir hata değil, asistanın güvenlik önlemidir. İzin sorarsa ne yapacağını okuyup onaylayın. Reddederse "
                  "ona bu aracı çalıştırmasına izin verdiğinizi açıkça yazın ya da asistanınızın izin ayarını “her komutta sor” "
                  "biçimine getirip yeniden deneyin. Asistan yine yapamazsa size çalıştırmanız gereken komutları verir.",
                  baslik="Asistanınız izin isterse ya da reddederse"))

    h.append(p("Kurulumdan sonra neler sorabilirsiniz", "h2"))
    h += maddeler([
        "“249 liralık telefon kılıfını hangi pazaryerinde satmalıyım? Maliyetim 80 lira.”",
        "“Trendyol'daki komisyon oranım %21,5. Buna göre 1.299 liralık montta elime ne kalır?”",
        "“Şu ürün listesinden pazar analizi çıkar ve tabloma yaz.” (ürünleri ad, marka, fiyat, puan, yorum sayısı olarak yazın "
        "ya da bir CSV/Excel dosyası verin)",
        "“Bu sonucu Excel dosyası olarak masaüstüme kaydet.”",
        "“Hangi kategoriler için komisyon verisi var?”",
    ])
    h.append(kutu("Komisyon oranları yaklaşık değerlerdir: pazaryerleri oranları herkese açık tek bir tabloda yayımlamaz. "
                  "Bağlayıcı oran, satıcı panelinizdeki sözleşme ekranında yazar. Kendi oranınızı asistana söylerseniz hesap "
                  "kesinleşir. Kargo, sabit hizmet bedeli, stopaj, reklam ve iade maliyeti hesaba dahil değildir.",
                  renk=SARI, baslik="Sonuçları okurken"))
    # ------------------------------------------------------------ asistan için kısa not
    # Asistanın izleyeceği ayrıntılı adımlar depodaki AGENTS.md dosyasındadır. Burada yalnızca oraya
    # ulaşması için gereken kadarı durur; kullanıcının bu kutuyla bir şey yapması gerekmez.
    h.append(Spacer(1, 6))
    h.append(
        kutu(f"Bu kılavuz sana verildiyse kullanıcı, burada anlatılan aracı bilgisayarına kurmanı ve onun adına "
             f"kullanmanı istiyor. Aracı şu adresten indir:<br/><font face='Kod' size='9'>git clone {DEPO}.git</font><br/>"
             f"(git yoksa: <font face='Kod' size='8'>{ZIP}</font>)<br/><br/>"
             "İndirdiğin klasörün kökündeki <b>AGENTS.md</b> dosyasını oku ve oradaki adımları sırayla izle: kurulum, "
             "doğrulama, Google Sheets bağlantısı ve kullanım komutları orada yazılıdır.<br/><br/>"
             "İki kural her zaman geçerli: rakamları kendin hesaplama, araçtan al; hizmet hesabı anahtar dosyasını "
             "açma ve içeriğini ekrana yazma, yalnızca yolunu araca ver.",
             baslik="Yapay zekâ asistanı için not"))

    # ------------------------------------------------------------ kapanış
    h.append(p("Bilmeniz gerekenler", "h1"))
    h.append(p("Verileriniz ve gizlilik", "h2"))
    h += maddeler([
        "Araç bilgisayarınızda çalışır. Girdiğiniz fiyat, maliyet ve ürün listesi aracın yazarına ya da başka bir sunucuya gönderilmez.",
        "Google Sheets çıktısını kullanırsanız sonuçlar yalnızca sizin belirttiğiniz Google tablosuna yazılır.",
        "Asistanınıza yazdıklarınız, kullandığınız asistanın kendi gizlilik koşullarına tabidir.",
        "Anahtar dosyası bilgisayarınızda, yalnızca sizin okuyabileceğiniz bir klasörde saklanır. Bağlantıyı kaldırmak için Google "
        "Cloud'daki hizmet hesabını silmeniz ya da tablonuzun paylaşımından o adresi çıkarmanız yeterlidir.",
    ])
    h.append(p("Sınırlar", "h2"))
    h += maddeler([
        "Komisyon oranları e-ticaret yazılım firmalarının yayımladığı listelerden 8 Ekim 2026'da derlenmiştir ve yaklaşıktır. "
        "Her oranın kaynağı proje sayfasındaki veri dosyasında yazılıdır.",
        "Yalnızca komisyon (ve n11'in oransal hizmet bedelleri) düşülür. Kargo, sabit hizmet bedeli, stopaj, reklam ve iade dahil değildir.",
        "Bazı kategorilerde Amazon ve n11 için oran verisi yoktur.",
        "Pazar analizi verdiğiniz listeyle sınırlıdır ve satış adedi ya da ciro tahmini içermez.",
        "Araç pazaryerlerinden veri çekmez; ürün listesini siz sağlarsınız.",
    ])
    h.append(p("Sorumluluk notu", "h2"))
    h.append(p("Bu araç Trendyol, Hepsiburada, n11 veya Amazon ile bağlantılı değildir ve onlar tarafından onaylanmamıştır. "
               "Sonuçlar bilgi amaçlıdır; fiyatlama veya yatırım kararı vermeden önce satıcı panelinizdeki güncel oranları "
               "kontrol edin. Yazılım açık kaynaktır ve MIT lisansıyla, garanti verilmeden sunulur."))
    h.append(Spacer(1, 10))
    h.append(kutu(f"Proje sayfası, kaynak kod ve asistansız kurulum adımları:<br/><b>{DEPO}</b><br/><br/>"
                  "Hata bildirmek ya da öneride bulunmak için proje sayfasındaki <b>Issues</b> bölümünü kullanabilirsiniz.",
                  baslik="Daha fazlası"))
    h.append(kutu(f"Bu araç ve kılavuz <b>{GELISTIREN}</b> tarafından geliştirilmiştir.<br/>"
                  f"E-posta: <b>{EPOSTA}</b> &nbsp;·&nbsp; Telefon: <b>{TELEFON}</b><br/><br/>"
                  "Kurulumda takıldığınız bir yer olursa ya da işletmenize özel bir analiz aracı isterseniz yazabilirsiniz.",
                  baslik="Geliştiren ve iletişim"))
    return h


def main():
    belge = SimpleDocTemplate(str(CIKTI), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
                              title="Pazar ve Komisyon Analizcisi — Asistanla kurulum ve kullanım kılavuzu",
                              author=GELISTIREN, subject="E-ticaret satıcıları için açık kaynak analiz aracı", lang="tr")
    belge.build(icerik(), onFirstPage=alt_bilgi, onLaterPages=alt_bilgi)
    print(CIKTI)


if __name__ == "__main__":
    main()
