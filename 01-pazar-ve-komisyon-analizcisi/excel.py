"""Sonuçları Excel dosyası (.xlsx) olarak yazar.

Çıkan dosya bir rapor olduğu kadar bir şablondur da: fiyat, maliyet ve komisyon oranları sarı
hücrelerdedir; onları değiştirdiğinizde komisyon, ele geçen tutar ve kâr Excel'in içinde yeniden
hesaplanır. Pazar sayfasındaki özetler de "Ürünler" sayfasındaki listeden formülle gelir.

Ek paket kullanılmaz: .xlsx, içinde XML dosyaları olan bir zip arşividir ve burada elle kurulur.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from xml.sax.saxutils import escape

from komisyon import Satir
from pazar import PazarRaporu, Urun

# ---------------------------------------------------------------- küçük xlsx yazıcı


@dataclass
class Formul:
    ifade: str  # baştaki "=" olmadan
    deger: float | str | None  # Excel açmadan önce görünecek hesaplanmış değer


# Biçem numaraları (styles.xml içindeki cellXfs sırası)
DUZ, BASLIK, SUTUN, ETIKET, GIRDI_TL, TL, GIRDI_YUZDE, YUZDE, TAM, NOT, SARMA, ONDALIK, VURGU_TL, GIRDI_METIN = range(14)

_STILLER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="3">
<numFmt numFmtId="164" formatCode="#,##0.00&quot; TL&quot;"/>
<numFmt numFmtId="165" formatCode="0.0%"/>
<numFmt numFmtId="166" formatCode="0.0"/>
</numFmts>
<fonts count="6">
<font><sz val="10"/><name val="Arial"/></font>
<font><b/><sz val="14"/><name val="Arial"/></font>
<font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Arial"/></font>
<font><b/><sz val="10"/><name val="Arial"/></font>
<font><sz val="10"/><color rgb="FF0000FF"/><name val="Arial"/></font>
<font><sz val="9"/><color rgb="FF595959"/><name val="Arial"/></font>
</fonts>
<fills count="5">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF1F3864"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFFFF00"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFDDEBF7"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="2">
<border><left/><right/><top/><bottom/><diagonal/></border>
<border><left/><right/><top/><bottom style="thin"><color rgb="FFBFBFBF"/></bottom><diagonal/></border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="14">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="2" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="164" fontId="4" fillId="3" borderId="1" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="165" fontId="4" fillId="3" borderId="1" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="165" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="3" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="0" fontId="5" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="166" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="164" fontId="3" fillId="4" borderId="1" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="0" fontId="4" fillId="3" borderId="1" xfId="0"/>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""


def _sutun_harfi(n: int) -> str:
    """1 → A, 27 → AA"""
    harf = ""
    while n:
        n, kalan = divmod(n - 1, 26)
        harf = chr(65 + kalan) + harf
    return harf


def _guvenli(metin: str) -> str:
    """Dışarıdan gelen metin (ürün ve marka adı) Excel'de formül olarak çalışmasın.

    "=", "+", "-", "@" ile başlayan hücreleri Excel formül sayabilir; başına görünmez olmayan bir
    kesme işareti konur. XML'de geçersiz denetim karakterleri de atılır.
    """
    metin = "".join(k for k in str(metin) if k in "\t\n" or ord(k) >= 32)
    if metin[:1] in ("=", "+", "-", "@"):
        metin = "'" + metin
    return metin


class Sayfa:
    def __init__(self, ad: str, genislikler: list[float], dondur: str | None = None):
        self.ad, self.genislikler, self.dondur = ad, genislikler, dondur
        self.satirlar: dict[int, list[tuple[int, object, int]]] = {}
        self.yukseklikler: dict[int, float] = {}
        self.birlesimler: list[str] = []

    def yaz(self, hucre: str, deger, bicem: int = DUZ) -> None:
        harfler = "".join(k for k in hucre if k.isalpha())
        satir = int(hucre[len(harfler):])
        sutun = 0
        for k in harfler:
            sutun = sutun * 26 + ord(k) - 64
        self.satirlar.setdefault(satir, []).append((sutun, deger, bicem))

    def satir(self, no: int, degerler: list, bicemler: list[int] | int = DUZ, bas: int = 1) -> None:
        for i, d in enumerate(degerler):
            b = bicemler if isinstance(bicemler, int) else bicemler[i]
            self.yaz(f"{_sutun_harfi(bas + i)}{no}", d, b)

    def birlestir(self, aralik: str, yukseklik: float | None = None) -> None:
        self.birlesimler.append(aralik)
        if yukseklik:
            self.yukseklikler[int("".join(k for k in aralik.split(":")[0] if k.isdigit()))] = yukseklik

    def xml(self) -> str:
        p = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">']
        if self.dondur:
            satir_no = int("".join(k for k in self.dondur if k.isdigit()))
            p.append(f'<sheetViews><sheetView workbookViewId="0"><pane ySplit="{satir_no - 1}" topLeftCell="{self.dondur}" '
                     f'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>')
        p.append("<cols>" + "".join(f'<col min="{i}" max="{i}" width="{g}" customWidth="1"/>'
                                    for i, g in enumerate(self.genislikler, 1)) + "</cols>")
        p.append("<sheetData>")
        for no in sorted(self.satirlar):
            yuk = f' ht="{self.yukseklikler[no]}" customHeight="1"' if no in self.yukseklikler else ""
            p.append(f'<row r="{no}"{yuk}>')
            for sutun, deger, bicem in sorted(self.satirlar[no], key=lambda h: h[0]):
                r = f"{_sutun_harfi(sutun)}{no}"
                if isinstance(deger, Formul):
                    f = escape(deger.ifade)
                    if isinstance(deger.deger, str):
                        p.append(f'<c r="{r}" s="{bicem}" t="str"><f>{f}</f><v>{escape(deger.deger)}</v></c>')
                    elif deger.deger is None:
                        p.append(f'<c r="{r}" s="{bicem}"><f>{f}</f></c>')
                    else:
                        p.append(f'<c r="{r}" s="{bicem}"><f>{f}</f><v>{deger.deger!r}</v></c>')
                elif deger is None or deger == "":
                    p.append(f'<c r="{r}" s="{bicem}"/>')
                elif isinstance(deger, bool):
                    p.append(f'<c r="{r}" s="{bicem}" t="inlineStr"><is><t>{"Evet" if deger else "Hayır"}</t></is></c>')
                elif isinstance(deger, (int, float)):
                    p.append(f'<c r="{r}" s="{bicem}"><v>{deger!r}</v></c>')
                else:
                    p.append(f'<c r="{r}" s="{bicem}" t="inlineStr"><is><t xml:space="preserve">{escape(_guvenli(deger))}</t></is></c>')
            p.append("</row>")
        p.append("</sheetData>")
        if self.birlesimler:
            p.append(f'<mergeCells count="{len(self.birlesimler)}">' + "".join(f'<mergeCell ref="{a}"/>' for a in self.birlesimler) + "</mergeCells>")
        p.append('<pageMargins left="0.5" right="0.5" top="0.6" bottom="0.6" header="0.3" footer="0.3"/>')
        p.append('<pageSetup orientation="landscape" fitToWidth="1" fitToHeight="0"/>')
        p.append("</worksheet>")
        return "".join(p)


def kitap_yaz(sayfalar: list[Sayfa]) -> bytes:
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                             for i in range(1, len(sayfalar) + 1)) + "</Types>")
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   "</Relationships>")
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{escape(s.ad)}" sheetId="{i}" r:id="rId{i}"/>' for i, s in enumerate(sayfalar, 1))
                   + '</sheets><calcPr fullCalcOnLoad="1"/></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
                             for i in range(1, len(sayfalar) + 1))
                   + f'<Relationship Id="rId{len(sayfalar) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                   "</Relationships>")
        z.writestr("xl/styles.xml", _STILLER)
        for i, s in enumerate(sayfalar, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", s.xml())
    return tampon.getvalue()


# ---------------------------------------------------------------- rapor sayfaları

ACIKLAMA = "Sarı hücreleri değiştirebilirsiniz; diğer hücreler kendiliğinden yeniden hesaplanır."


def komisyon_sayfasi(kategori_adi: str, fiyat: float, maliyet: float | None, satirlar: list[Satir], veri: dict,
                     fiyat_formulu: Formul | None = None) -> Sayfa:
    """Komisyon karşılaştırması. Fiyat B4, maliyet B5; oranlar tabloda sarı hücrelerde."""
    s = Sayfa("Komisyon", [24, 13, 13, 12, 16, 16, 17, 17, 16, 16, 70], dondur="A9")
    s.yaz("A1", "Komisyon Karşılaştırması", BASLIK)
    s.yaz("A2", ACIKLAMA, NOT)
    s.birlestir("A2:K2")
    s.yaz("A3", "Kategori", ETIKET)
    s.yaz("B3", kategori_adi, GIRDI_METIN)
    s.birlestir("B3:D3")
    s.yaz("A4", "Satış fiyatı", ETIKET)
    s.yaz("B4", fiyat_formulu if fiyat_formulu else fiyat, TL if fiyat_formulu else GIRDI_TL)
    if fiyat_formulu:
        s.yaz("C4", "Pazar sayfasındaki ortanca fiyattan gelir; kendi fiyatınızı yazarak değiştirebilirsiniz.", NOT)
        s.birlestir("C4:K4")
    s.yaz("A5", "Ürün maliyeti", ETIKET)
    s.yaz("B5", maliyet, GIRDI_TL)
    s.yaz("C5", "Boş bırakırsanız kâr hesaplanmaz.", NOT)
    s.birlestir("C5:K5")

    s.satir(8, ["Pazaryeri", "Oran (en düşük)", "Oran (en yüksek)", "Ek kesinti", "Komisyon (en az)", "Komisyon (en çok)",
                "Elinize geçen (en az)", "Elinize geçen (en çok)", "Kârınız (en az)", "Kârınız (en çok)", "Not"], SUTUN)
    s.yukseklikler[8] = 30
    for i, x in enumerate(satirlar):
        r = 9 + i
        var = x.oran_min is not None
        s.yaz(f"A{r}", x.ad, ETIKET)
        s.yaz(f"B{r}", x.oran_min / 100 if var else None, GIRDI_YUZDE)
        s.yaz(f"C{r}", x.oran_max / 100 if var else None, GIRDI_YUZDE)
        s.yaz(f"D{r}", x.ek_kesinti_orani / 100 if var else veri["pazaryerleri"][x.pazaryeri].get("ek_kesinti_orani", 0) / 100, GIRDI_YUZDE)
        bos = f'OR(B{r}="",C{r}="")'
        s.yaz(f"E{r}", Formul(f'IF({bos},"veri yok",$B$4*B{r})', x.komisyon_min if var else "veri yok"), TL)
        s.yaz(f"F{r}", Formul(f'IF({bos},"veri yok",$B$4*C{r})', x.komisyon_max if var else "veri yok"), TL)
        s.yaz(f"G{r}", Formul(f'IF({bos},"veri yok",$B$4-F{r}-$B$4*D{r})', x.ele_gecen_min if var else "veri yok"), VURGU_TL)
        s.yaz(f"H{r}", Formul(f'IF({bos},"veri yok",$B$4-E{r}-$B$4*D{r})', x.ele_gecen_max if var else "veri yok"), VURGU_TL)
        kar_yok = "" if var else "veri yok"
        s.yaz(f"I{r}", Formul(f'IF({bos},"veri yok",IF($B$5="","",G{r}-$B$5))', x.kar_min if x.kar_min is not None else kar_yok), TL)
        s.yaz(f"J{r}", Formul(f'IF({bos},"veri yok",IF($B$5="","",H{r}-$B$5))', x.kar_max if x.kar_max is not None else kar_yok), TL)
        notu = x.notu if var else "Bu kategori için oran bulunamadı. Sözleşmenizdeki oranı sarı hücrelere yazabilirsiniz."
        if x.kaynak == "satıcının girdiği oran":
            notu = "Sizin girdiğiniz oran kullanıldı. " + notu
        s.yaz(f"K{r}", notu, SARMA)
        s.yukseklikler[r] = 42

    r = 9 + len(satirlar) + 1
    notlar = [
        "Oranlar ondalık yüzde olarak yazılır (ör. %21,5). En düşük ve en yüksek oran aynıysa tek bir oran var demektir.",
        "Kargo, sabit hizmet bedeli, stopaj, reklam ve iade maliyeti hesaba dahil değildir; gerçekte elinize geçen tutar daha düşük olur.",
        f"Oranlar yaklaşık değerlerdir (derleme tarihi: {veri['_derleme_tarihi']}). Bağlayıcı oran, satıcı panelinizdeki sözleşme ekranında yazar.",
        "Bu dosya herhangi bir pazaryeriyle bağlantılı değildir; bilgi amaçlıdır.",
    ]
    adresler = sorted({a for x in satirlar for a in x.kaynak_adresleri})
    if adresler:
        notlar.append("Oran kaynakları: " + "  |  ".join(adresler))
    for n in notlar:
        s.yaz(f"A{r}", n, NOT)
        s.birlestir(f"A{r}:K{r}", yukseklik=28 if len(n) > 150 else None)
        r += 1
    return s


def urunler_sayfasi(urunler: list[Urun]) -> Sayfa:
    s = Sayfa("Ürünler", [48, 22, 14, 9, 12], dondur="A2")
    s.satir(1, ["Ürün", "Marka", "Fiyat", "Puan", "Yorum sayısı"], SUTUN)
    for i, u in enumerate(urunler, 2):
        s.satir(i, [u.ad, u.marka or "", u.fiyat, u.puan, u.yorum], [SARMA, SARMA, TL, ONDALIK, TAM])
    return s


def pazar_sayfasi(r: PazarRaporu, urun_sayisi: int) -> Sayfa:
    """Pazar özeti. Sayılar 'Ürünler' sayfasındaki listeden formülle hesaplanır."""
    son = urun_sayisi + 1
    fiyat, puan, yorum, marka = (f"'Ürünler'!$C$2:$C${son}", f"'Ürünler'!$D$2:$D${son}", f"'Ürünler'!$E$2:$E${son}",
                                 f"'Ürünler'!$B$2:$B${son}")
    s = Sayfa("Pazar", [34, 18, 18, 26, 4, 4], dondur=None)
    s.yaz("A1", "Pazar Analizi", BASLIK)
    s.yaz("A2", "Özetler “Ürünler” sayfasındaki listeden hesaplanır; oradaki fiyatları değiştirirseniz güncellenir.", NOT)
    s.birlestir("A2:D2")

    s.satir(4, ["Fiyat", "Değer"], SUTUN)
    kalemler = [
        ("İncelenen ürün sayısı", Formul(f"COUNT({fiyat})", r.urun_sayisi), TAM),
        ("En düşük fiyat", Formul(f"MIN({fiyat})", r.fiyat_min), TL),
        ("Alt çeyrek", Formul(f"QUARTILE({fiyat},1)", r.fiyat_ceyrek1), TL),
        ("Ortanca fiyat", Formul(f"MEDIAN({fiyat})", r.fiyat_medyan), VURGU_TL),
        ("Üst çeyrek", Formul(f"QUARTILE({fiyat},3)", r.fiyat_ceyrek3), TL),
        ("En yüksek fiyat", Formul(f"MAX({fiyat})", r.fiyat_max), TL),
        ("Ortalama fiyat", Formul(f"AVERAGE({fiyat})", r.fiyat_ortalama), TL),
    ]
    for i, (ad, f, b) in enumerate(kalemler, 5):
        s.yaz(f"A{i}", ad, ETIKET)
        s.yaz(f"B{i}", f, b)
    ORTANCA_HUCRE = "B8"

    satir = 13
    s.satir(satir, ["Fiyat bandı (alt sınır)", "Üst sınır", "Ürün sayısı", "Ürün başına ortalama yorum"], SUTUN)
    for i, b in enumerate(r.bantlar):
        n = satir + 1 + i
        son_bant = i == len(r.bantlar) - 1
        ust_islec = "<=" if son_bant else "<"
        s.yaz(f"A{n}", b.alt, TL)
        s.yaz(f"B{n}", b.ust, TL)
        kosul = f'{fiyat},">="&A{n},{fiyat},"{ust_islec}"&B{n}'
        s.yaz(f"C{n}", Formul(f"COUNTIFS({kosul})", b.urun_sayisi), TAM)
        s.yaz(f"D{n}", Formul(f'IFERROR(AVERAGEIFS({yorum},{kosul}),"-")', b.ortalama_yorum if b.ortalama_yorum is not None else "-"), TAM)
    satir += len(r.bantlar) + 2

    if r.markalar:
        s.satir(satir, ["Öne çıkan markalar", "Ürün sayısı", "Payı"], SUTUN)
        for i, (m, adet, pay) in enumerate(r.markalar):
            n = satir + 1 + i
            s.yaz(f"A{n}", m, SARMA)
            s.yaz(f"B{n}", Formul(f"COUNTIF({marka},A{n})", adet), TAM)
            s.yaz(f"C{n}", Formul(f"B{n}/$B$5", pay / 100), YUZDE)
        satir += len(r.markalar) + 2

    s.satir(satir, ["İlgi ve rekabet", "Değer"], SUTUN)
    satir += 1
    if r.puan_medyan is not None:
        s.yaz(f"A{satir}", "Ortanca puan", ETIKET)
        s.yaz(f"B{satir}", Formul(f"MEDIAN({puan})", r.puan_medyan), ONDALIK)
        satir += 1
    if r.yorum_medyan is not None:
        s.yaz(f"A{satir}", "Ortanca yorum sayısı", ETIKET)
        s.yaz(f"B{satir}", Formul(f"MEDIAN({yorum})", r.yorum_medyan), TAM)
        satir += 1
    if r.ilk10_yorum_payi is not None:
        s.yaz(f"A{satir}", "En çok yorumlanan 10 ürünün yorum payı", ETIKET)
        s.yaz(f"B{satir}", Formul(f"SUMPRODUCT(LARGE({yorum},{{1,2,3,4,5,6,7,8,9,10}}))/SUM({yorum})", r.ilk10_yorum_payi / 100), YUZDE)
        s.yaz(f"C{satir}", f"Pazar {r.yogunluk}", DUZ)
        satir += 1
    if r.yorum_medyan is None:
        s.yaz(f"A{satir}", "Listede yorum sayısı olmadığı için hesaplanmadı.", NOT)
        satir += 1
    satir += 1

    s.yaz(f"A{satir}", "Okuma", ETIKET)
    satir += 1
    okuma = []
    if r.yogunluk == "yoğunlaşmış":
        okuma.append("İlgi birkaç üründe toplanmış; yeni bir ürünün görünür olması zor, fiyat veya farklılaşma gerekir.")
    elif r.yogunluk == "orta":
        okuma.append("İlgi birkaç güçlü ürünle geri kalanlar arasında bölünmüş; öne çıkmak mümkün ama yorum birikimi gerekir.")
    elif r.yogunluk == "dağınık":
        okuma.append("İlgi ürünlere yayılmış; tek bir hâkim ürün yok, yeni girişe görece açık.")
    if r.bosluk:
        okuma.append(f"{r.bosluk.alt:,.0f} – {r.bosluk.ust:,.0f} TL bandında yalnızca {r.bosluk.urun_sayisi} ürün var, ama ürün başına "
                     "yorum ortancanın üstünde: bu bant az rakipli ve ilgi görüyor.".replace(",", "."))
    else:
        okuma.append("Belirgin biçimde boş kalan ve ilgi gören bir fiyat bandı görünmüyor.")
    okuma += list(r.uyarilar)
    okuma.append("“Okuma” satırları dosya oluşturulurken yazılmıştır; listeyi değiştirirseniz bu cümleler güncellenmez.")
    okuma.append("Bu analiz yalnızca listedeki ürünleri kapsar. Satış adedi ve ciro bilgisi içermez; yorum sayısı ilginin dolaylı göstergesidir.")
    for o in okuma:
        s.yaz(f"A{satir}", o, NOT)
        s.birlestir(f"A{satir}:D{satir}", yukseklik=26 if len(o) > 95 else None)
        satir += 1
    s.ortanca_hucre = ORTANCA_HUCRE
    return s


def komisyon_dosyasi(kategori_adi: str, fiyat: float, maliyet: float | None, satirlar: list[Satir], veri: dict) -> bytes:
    return kitap_yaz([komisyon_sayfasi(kategori_adi, fiyat, maliyet, satirlar, veri)])


def pazar_dosyasi(rapor: PazarRaporu, urunler: list[Urun], komisyon: tuple | None, veri: dict) -> bytes:
    """`komisyon` verilirse (kategori_adi, maliyet, satirlar) üçlüsüdür; fiyat, pazarın ortancasına bağlanır."""
    urunler = [u for u in urunler if u.fiyat and u.fiyat > 0]
    pazar = pazar_sayfasi(rapor, len(urunler))
    sayfalar = [pazar, urunler_sayfasi(urunler)]
    if komisyon:
        kategori_adi, maliyet, satirlar = komisyon
        bag = Formul(f"'Pazar'!{pazar.ortanca_hucre}", rapor.fiyat_medyan)
        sayfalar.insert(1, komisyon_sayfasi(kategori_adi, rapor.fiyat_medyan, maliyet, satirlar, veri, fiyat_formulu=bag))
    return kitap_yaz(sayfalar)
