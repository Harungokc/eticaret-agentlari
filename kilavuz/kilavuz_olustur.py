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
PAKET_ADI = "pazar-komisyon-analizcisi.zip"
PAKET = DEPO + "/releases/latest/download/" + PAKET_ADI

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
    "adimbaslik": ParagraphStyle("adimbaslik", fontName="Govde-Kalin", fontSize=10.5, leading=15, spaceBefore=6, spaceAfter=3,
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
          p("Claude ve ChatGPT ile kurulum ve kullanım kılavuzu", "kapak_alt")]
    h += gelistiren_kutusu()
    h.append(kutu(
        "Bu araç <b>Claude</b> ya da <b>ChatGPT</b> sohbet ekranında çalışır; kod bilmeniz ya da bilgisayarınıza program "
        "kurmanız gerekmez. <b>1)</b> Paket dosyasını indirin. <b>2)</b> Claude'a ya da ChatGPT'ye yükleyin. <b>3)</b> Konuşur "
        "gibi sorun: <i>“899 liralık kadın ayakkabıyı hangi pazaryerinde satmalıyım?”</i> Asistan hesabı araçla yapar, "
        "sonucu anlatır ve size bir Excel dosyası verir.",
        baslik="Bu kılavuz nasıl kullanılır"))

    h.append(p("Araç ne yapar", "h2"))
    h += maddeler([
        "<b>Komisyon karşılaştırması:</b> Kategori ve satış fiyatına göre Trendyol, Hepsiburada, n11 ve Amazon Türkiye'nin "
        "keseceği komisyonu, elinize geçecek tutarı ve kârınızı yan yana gösterir.",
        "<b>Pazar analizi:</b> Bir ürün listesinden fiyat bantlarını, öne çıkan markaları, rekabet yoğunluğunu ve az rakipli "
        "fiyat aralığını çıkarır.",
        "<b>Excel ve Google Sheets çıktısı:</b> Sonuçları Excel dosyası olarak verir; dosyayı Google Sheets'te de açabilirsiniz. "
        "Tablodaki sarı hücreleri (fiyat, maliyet, oranlar) değiştirdiğinizde sonuçlar kendiliğinden yeniden hesaplanır.",
    ])

    h.append(p("Örnek bir konuşma", "h2"))
    h += tablo(["Siz", "Asistan"], [
        ["899 liralık kadın ayakkabı satacağım, maliyetim 400 lira. Hangi pazaryeri daha kârlı?",
         "Hesabı yaptım. Hepsiburada'da elinize 724–737 TL, n11'de 698–746 TL, Trendyol'da 697–706 TL geçiyor. Ortalamada "
         "Hepsiburada önde, ama n11'in oran aralığı onunla çakışıyor; kesin sıralama için sözleşmenizdeki oranları söylerseniz "
         "yeniden hesaplarım. Kargo ve diğer kesintiler bu hesaba dahil değil. Sonucu Excel dosyası olarak ekledim."],
    ], [0.38, 0.62])

    h.append(p("Gerekenler", "h2"))
    h += maddeler([
        "Bir <b>Claude</b> ya da <b>ChatGPT</b> hesabı. Dosya yükleme ve kod çalıştırma özelliği gerekir; bu özellik Claude'da "
        "ücretli planlarda, ChatGPT'de ücretli planlarda ve sınırlı olarak ücretsiz planda bulunur.",
        f"Paket dosyası: <b>{PAKET_ADI}</b> (Kurulum bölümündeki adresten indirilir, 34 KB)",
    ])

    h.append(PageBreak())
    h.append(p("Sonuç tablonuzda böyle görünür", "h2"))
    h.append(p("Aşağıdaki görüntüler aracın Google Sheets'e doğrudan yazdığı gerçek sayfalardır. Excel dosyasında aynı tablolar "
               "ve formüller bulunur, grafikler bulunmaz. İçlerindeki ürün ve markalar örnek amaçlı uydurma verilerdir."))
    h.append(gorsel("google-sheets-komisyon.png", "Komisyon sayfası: sarı hücreleri değiştirdiğinizde tablo yeniden hesaplanır."))
    h.append(gorsel("google-sheets-pazar.png", "Pazar sayfası: fiyat özeti, fiyat bantları ve öne çıkan markalar."))

    # ------------------------------------------------------------ kurulum
    h.append(PageBreak())
    h.append(p("Kurulum", "h1"))
    h.append(p("Önce paket dosyasını bilgisayarınıza indirin. Dosyayı açmanıza (ZIP'ten çıkarmanıza) gerek yoktur:"))
    h.append(kutu(f"<a href='{PAKET}' color='#1F4FD8'><font face='Kod' size='7.6'>{PAKET}</font></a>"))

    h.append(p("Claude kullanıyorsanız", "h2"))
    h.append(p("Paketi bir kez “Skill” (beceri) olarak eklersiniz; sonrasında her sohbette hazırdır."))
    h += maddeler([
        "claude.ai adresini ya da Claude uygulamasını açın.",
        "<b>Settings → Capabilities</b> (Ayarlar → Yetenekler) sayfasında <b>Code execution and file creation</b> "
        "(Kod yürütme ve dosya oluşturma) seçeneğinin açık olduğunu denetleyin.",
        "<b>Customize → Skills</b> (Özelleştir → Beceriler) sayfasına gidin, <b>+</b> düğmesine basıp <b>Upload a skill</b> "
        f"(Beceri yükle) deyin ve indirdiğiniz <b>{PAKET_ADI}</b> dosyasını seçin.",
        "Listede “pazar-komisyon-analizcisi” göründüğünde açık olduğundan emin olun.",
        "Yeni bir sohbet açın ve sorunuzu yazın. İlk seferde şunu deneyin: <i>“Pazar ve komisyon analizcisiyle 899 liralık "
        "kadın ayakkabı için pazaryerlerini karşılaştır, maliyetim 400 lira.”</i>",
    ], numarali=True)

    h.append(p("ChatGPT kullanıyorsanız", "h2"))
    h.append(p("Paketi sohbete dosya olarak yüklersiniz."))
    h += maddeler([
        "chatgpt.com adresini ya da ChatGPT uygulamasını açın ve yeni bir sohbet başlatın.",
        f"Mesaj kutusundaki <b>+</b> (dosya ekle) düğmesiyle <b>{PAKET_ADI}</b> dosyasını yükleyin.",
        "Aşağıdaki mesajı gönderin:",
    ], numarali=True)
    h.append(kod("""
Bu ZIP dosyasını aç, içindeki SKILL.md dosyasını oku ve oradaki talimatlara göre çalış.
Önce örnek bir komisyon hesabıyla aracın çalıştığını göster.
"""))
    h.append(p("ChatGPT yüklenen dosyayı sohbet bitince saklamaz; yeni bir sohbette paketi yeniden yüklersiniz. Her seferinde "
               "yüklemek istemezseniz paketi bir <b>Proje</b>'ye ya da kendi <b>GPT</b>'nize dosya olarak ekleyebilirsiniz."))

    h.append(p("Sonucu Google Sheets'te açmak", "h2"))
    h += maddeler([
        "Asistanın verdiği Excel dosyasını indirin.",
        "Tarayıcınızda <b>sheets.new</b> adresini açın.",
        "<b>Dosya → İçe aktar → Yükle</b> deyin ve Excel dosyasını seçin. Formüller çalışmaya devam eder.",
    ], numarali=True)
    h.append(kutu("Paket ek kurulum ve internet bağlantısı gerektirmez; yalnızca Python ile çalışır. Asistanınız paketi "
                  "çalıştıramadığını söylerse hesabı kendi başına yapmasına izin vermeyin; rakamlar araçtan gelmelidir. "
                  "Sorunu son sayfadaki iletişim adresine yazabilirsiniz.",
                  renk=SARI, baslik="Asistan aracı çalıştıramazsa"))

    h.append(p("Neler sorabilirsiniz", "h2"))
    h += maddeler([
        "“249 liralık telefon kılıfını hangi pazaryerinde satmalıyım? Maliyetim 80 lira.”",
        "“Trendyol'daki komisyon oranım %21,5. Buna göre 1.299 liralık montta elime ne kalır?”",
        "“Şu ürün listesinden pazar analizi çıkar.” (ürünleri ad, marka, fiyat, puan, yorum sayısı olarak yazın ya da bir "
        "dosya yükleyin; en az 8 ürün gerekir)",
        "“Hangi kategoriler için komisyon verisi var?”",
    ])
    h.append(kutu("Komisyon oranları yaklaşık değerlerdir: pazaryerleri oranları herkese açık tek bir tabloda yayımlamaz. "
                  "Bağlayıcı oran, satıcı panelinizdeki sözleşme ekranında yazar. Kendi oranınızı asistana söylerseniz komisyon "
                  "hesabı o orana göre yapılır. Kargo, sabit hizmet bedeli, stopaj, reklam ve iade maliyeti hesaba dahil değildir.",
                  renk=SARI, baslik="Sonuçları okurken"))

    # ------------------------------------------------------------ kapanış
    h.append(p("Bilmeniz gerekenler", "h1"))
    h.append(p("Verileriniz ve gizlilik", "h2"))
    h += maddeler([
        "Araç, asistanınızın kod çalıştırma ortamında çalışır: Claude ve ChatGPT sohbetinde o şirketlerin sunucularındaki "
        "geçici ortamda, Claude Code ve Codex'te kendi bilgisayarınızda. Girdiğiniz fiyat, maliyet ve ürün listesi aracın "
        "yazarına gönderilmez.",
        "Paket internete bağlanmaz. Yalnızca Ek bölümündeki doğrudan Google Sheets yolunu kullanırsanız Google'a bağlanır ve "
        "sonuçları yalnızca sizin belirttiğiniz tabloya yazar.",
        "Asistanınıza yazdıklarınız, kullandığınız asistanın kendi gizlilik koşullarına tabidir.",
        "Ek bölümündeki yolu kullanırsanız anahtar dosyasının bir kopyası aracın çalıştığı yerde saklanır: kendi bilgisayarınızda ya da Cowork kullanıyorsanız "
        "görev süresince Cowork'ün geçici ortamında. Bağlantıyı kaldırmak için Google Cloud'daki hizmet hesabını ya da anahtarını silmeniz veya "
        "tablonuzun paylaşımından o adresi çıkarmanız yeterlidir.",
    ])
    h.append(p("Sınırlar", "h2"))
    h += maddeler([
        "Komisyon oranları e-ticaret yazılım firmalarının yayımladığı listelerden 8 Ekim 2026'da derlenmiştir ve yaklaşıktır. "
        "Her oranın kaynağı proje sayfasındaki veri dosyasında yazılıdır.",
        "Yalnızca komisyon (ve n11'in oransal hizmet bedelleri) düşülür. Kargo, sabit hizmet bedeli, stopaj, reklam ve iade dahil değildir.",
        "Bazı kategorilerde Amazon ve n11 için oran verisi yoktur.",
        "Pazar analizi verdiğiniz listeyle sınırlıdır ve satış adedi ya da ciro tahmini içermez.",
        "Araç pazaryerlerinden veri çekmez; ürün listesini siz sağlarsınız.",
        "Excel dosyasında grafik yoktur; grafikler yalnızca Ek bölümündeki doğrudan Google Sheets yolunda eklenir.",
    ])
    h.append(p("Sorumluluk notu", "h2"))
    h.append(p("Bu araç Trendyol, Hepsiburada, n11 veya Amazon ile bağlantılı değildir ve onlar tarafından onaylanmamıştır. "
               "Sonuçlar bilgi amaçlıdır; fiyatlama veya yatırım kararı vermeden önce satıcı panelinizdeki güncel oranları "
               "kontrol edin. Yazılım açık kaynaktır ve MIT lisansıyla, garanti verilmeden sunulur."))
    h.append(Spacer(1, 10))
    h.append(kutu(f"Proje sayfası, kaynak kod ve kendi bilgisayarınıza kurulum adımları:<br/><b>{DEPO}</b><br/><br/>"
                  "Hata bildirmek ya da öneride bulunmak için proje sayfasındaki <b>Issues</b> bölümünü kullanabilirsiniz.",
                  baslik="Daha fazlası"))
    h.append(kutu(f"Bu araç ve kılavuz <b>{GELISTIREN}</b> tarafından geliştirilmiştir.<br/>"
                  f"E-posta: <b>{EPOSTA}</b> &nbsp;·&nbsp; Telefon: <b>{TELEFON}</b><br/><br/>"
                  "Kurulumda takıldığınız bir yer olursa ya da işletmenize özel bir analiz aracı isterseniz yazabilirsiniz.",
                  baslik="Geliştiren ve iletişim"))
    # ------------------------------------------------------------ ek: doğrudan Google Sheets
    h.append(PageBreak())
    h.append(p("Ek — Sonuçları doğrudan Google Sheets'e, grafiklerle yazdırmak", "h1"))
    h.append(p("Bu bölüm isteğe bağlıdır ve <b>Claude Cowork</b>, <b>Claude Code</b> ya da <b>OpenAI Codex</b> gibi, komut "
               "çalıştırabilen ve internete çıkabilen asistanlar içindir. Bu yolda asistan aracı GitHub'dan kendisi indirir, "
               "sonuçları tablonuza kendisi yazar ve grafikleri ekler; ikinci sayfadaki görüntüler bu yolla üretilmiştir."))
    h += tablo(["Asistan", "Nerede çalışır", "Bilmeniz gereken"], [
        ["<b>Claude Cowork</b>",
         "Anthropic'in sunucularında, her görev için açılan geçici bir ortamda. Bilgisayarınızdaki dosyalara, "
         "bağladığınız klasörler üzerinden erişir.",
         "Anahtar dosyasını Cowork'e bağladığınız klasöre koyun. Ortam geçici olduğu için asistan aracı her yeni görevde "
         "yeniden indirir; bu bir dakikadan kısa sürer. Team ve Enterprise planlarında yöneticinizin ağ erişimini açması "
         "gerekebilir."],
        ["<b>Claude Code</b>, <b>OpenAI Codex</b>",
         "Kendi bilgisayarınızda",
         "Komut çalıştırmadan ve internete çıkmadan önce sizden onay ister. Codex'te ağ erişimi başlangıçta kapalıdır; "
         "asistan izin istediğinde onaylayın."],
    ], [0.27, 0.27, 0.46])
    h.append(p("Bu yolun kurulum adımları Claude Code ile macOS üzerinde denenmiştir.", "kucuk"))

    # ------------------------------------------------------------ bölüm A
    h.append(p("A. Sizin yapacağınız iş: Google Sheets bağlantısı", "h2"))
    h.append(p("Bu bölümü asistan sizin yerinize yapamaz, çünkü Google hesabınıza giriş gerektirir. Bir kez yapılır ve "
               "yaklaşık 10 dakika sürer."))
    h.append(kutu("Aracın tablonuza yazabilmesi için ona ait bir “robot hesap” (hizmet hesabı) oluşturur, bu hesabın anahtar "
                  "dosyasını indirir ve tablonuzu o hesapla paylaşırsınız. Araç yalnızca paylaştığınız tabloya erişebilir.",
                  baslik="Ne yapıyoruz"))

    h.append(p("<b>1. Proje oluşturun</b>", "adimbaslik"))
    h += maddeler([
        "Tarayıcınızda <b>console.cloud.google.com</b> adresini açın ve Google hesabınızla giriş yapın.",
        "Sayfanın üstündeki proje seçicisine tıklayın ve <b>New Project</b> (Yeni proje) deyin.",
        "Bir ad verin (örneğin “E-ticaret”) ve <b>Create</b> (Oluştur) düğmesine basın. Proje seçili hâle gelsin.",
    ], numarali=True)

    h.append(p("<b>2. Google Sheets API'yi açın</b>", "adimbaslik"))
    h += maddeler([
        "Üstteki arama kutusuna <b>Google Sheets API</b> yazın ve çıkan sonuca tıklayın.",
        "<b>Enable</b> (Etkinleştir) düğmesine basın.",
    ], numarali=True)

    h.append(CondPageBreak(45 * mm))
    h.append(p("<b>3. Hizmet hesabını oluşturun</b>", "adimbaslik"))
    h += maddeler([
        "Sol üstteki menüden <b>IAM &amp; Admin → Service Accounts</b> (IAM ve Yönetici → Hizmet Hesapları) sayfasına gidin.",
        "<b>+ Create service account</b> düğmesine basın.",
        "Bir ad yazın (örneğin “tablo-yazici”) ve <b>Create and continue</b> deyin.",
        "Rol seçme adımını boş bırakıp <b>Done</b> (Bitti) düğmesine basın. Rol vermenize gerek yoktur.",
    ], numarali=True)

    h.append(p("<b>4. Anahtar dosyasını indirin</b>", "adimbaslik"))
    h += maddeler([
        "Listede yeni oluşan hesabın adına tıklayın.",
        "Üstteki <b>Keys</b> (Anahtarlar) sekmesine geçin.",
        "<b>Add key → Create new key</b> deyin, <b>JSON</b> seçili kalsın ve <b>Create</b> düğmesine basın.",
        "Bilgisayarınıza <b>.json</b> uzantılı bir dosya iner. Nereye indiğini not edin (genellikle İndirilenler klasörü).",
    ], numarali=True)
    h.append(kutu("Bu dosya tablonuza erişim şifresi gibidir. Kimseyle paylaşmayın, sohbete içeriğini yapıştırmayın ve "
                  "e-postayla göndermeyin. Asistanınıza yalnızca dosyanın bilgisayarınızdaki <b>yerini</b> söyleyeceksiniz.",
                  renk=SARI, baslik="Anahtar dosyasını koruyun"))

    h.append(p("<b>5. Tablonuzu hizmet hesabıyla paylaşın</b>", "adimbaslik"))
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
    h.append(p("B. Asistanınıza vereceğiniz ilk mesaj", "h2"))
    h.append(p("Bu PDF'i asistanınıza ekleyin ve aşağıdaki mesajı, köşeli parantezli yerleri doldurarak gönderin."))
    h.append(kod("""
Ekteki kılavuzda anlatılan aracı kur, testlerini çalıştır
ve örnek bir komisyon hesabıyla çalıştığını göster.

Google Sheets bağlantımı da kur:
- Tablo adresim: [tablonuzun adresi]
- Anahtar dosyam: [anahtar dosyasının yeri, ör. ~/Downloads/proje-abc123.json]

Anahtar dosyasının içeriğini ekrana yazma.
"""))
    h.append(p("Asistan aracı indirir, kurar, dener ve tablonuza bağlar."))
    h.append(kutu("Asistanınız internetten indirdiği bir programı çalıştırmadan ya da tablonuza yazmadan önce sizden <b>izin "
                  "ister</b>; bazı ayarlarda ise bu adımı kendiliğinden <b>reddeder</b> ve “indirilen programı çalıştıramıyorum” "
                  "der. Bu bir hata değil, asistanın güvenlik önlemidir. İzin sorarsa ne yapacağını okuyup onaylayın. Reddederse "
                  "ona bu aracı çalıştırmasına izin verdiğinizi açıkça yazın ya da asistanınızın izin ayarını “her komutta sor” "
                  "biçimine getirip yeniden deneyin. Asistan yine yapamazsa size çalıştırmanız gereken komutları verir.",
                  baslik="Asistanınız izin isterse ya da reddederse"))

    # ------------------------------------------------------------ asistan için kısa not
    # Asistanın izleyeceği ayrıntılı adımlar depodaki AGENTS.md dosyasındadır. Burada yalnızca oraya
    # ulaşması için gereken kadarı durur; kullanıcının bu kutuyla bir şey yapması gerekmez.
    h.append(Spacer(1, 6))
    h.append(
        kutu(f"Bu kılavuz sana verildiyse kullanıcı, burada anlatılan aracı çalıştığın ortama kurmanı ve onun adına "
             f"kullanmanı istiyor. Aracı şu adresten indir:<br/><font face='Kod' size='9'>git clone {DEPO}.git</font><br/>"
             f"(git yoksa: <font face='Kod' size='8'>{ZIP}</font>)<br/><br/>"
             "İndirdiğin klasörün kökündeki <b>AGENTS.md</b> dosyasını oku ve oradaki adımları sırayla izle: kurulum, "
             "doğrulama, Google Sheets bağlantısı ve kullanım komutları orada yazılıdır.<br/><br/>"
             "İki kural her zaman geçerli: rakamları kendin hesaplama, araçtan al; hizmet hesabı anahtar dosyasını "
             "açma ve içeriğini ekrana yazma, yalnızca yolunu araca ver.",
             baslik="Yapay zekâ asistanı için not"))

    return h


def main():
    belge = SimpleDocTemplate(str(CIKTI), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
                              title="Pazar ve Komisyon Analizcisi — Asistanla kurulum ve kullanım kılavuzu",
                              author=GELISTIREN, subject="E-ticaret satıcıları için açık kaynak analiz aracı", lang="tr")
    belge.build(icerik(), onFirstPage=alt_bilgi, onLaterPages=alt_bilgi)
    print(CIKTI)


if __name__ == "__main__":
    main()
