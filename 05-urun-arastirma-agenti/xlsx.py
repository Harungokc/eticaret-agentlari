"""Küçük bir Excel (.xlsx) yazıcısı.

Ek paket kullanılmaz: .xlsx, içinde XML dosyaları olan bir zip arşividir ve burada elle kurulur.
Formüller hesaplanmış değerleriyle birlikte yazılır; dosya açıldığında Excel yeniden hesaplar.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from xml.sax.saxutils import escape

# ---------------------------------------------------------------- küçük xlsx yazıcı


@dataclass
class Formul:
    ifade: str  # baştaki "=" olmadan
    deger: float | str | None  # Excel açmadan önce görünecek hesaplanmış değer


# Biçem numaraları (styles.xml içindeki cellXfs sırası)
DUZ, BASLIK, SUTUN, ETIKET, GIRDI_TL, TL, GIRDI_YUZDE, YUZDE, TAM, NOT, SARMA, ONDALIK, VURGU_TL, GIRDI_METIN, AFIS = range(15)

_STILLER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="3">
<numFmt numFmtId="164" formatCode="#,##0.00&quot; TL&quot;"/>
<numFmt numFmtId="165" formatCode="0.0#%"/>
<numFmt numFmtId="166" formatCode="0.0"/>
</numFmts>
<fonts count="7">
<font><sz val="10"/><name val="Arial"/></font>
<font><b/><sz val="14"/><name val="Arial"/></font>
<font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Arial"/></font>
<font><b/><sz val="10"/><name val="Arial"/></font>
<font><sz val="10"/><color rgb="FF0000FF"/><name val="Arial"/></font>
<font><sz val="9"/><color rgb="FF595959"/><name val="Arial"/></font>
<font><b/><sz val="15"/><color rgb="FFFFFFFF"/><name val="Arial"/></font>
</fonts>
<fills count="5">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF1F3864"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFDDEBF7"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="2">
<border><left/><right/><top/><bottom/><diagonal/></border>
<border><left/><right/><top/><bottom style="thin"><color rgb="FFBFBFBF"/></bottom><diagonal/></border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="15">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="2" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="164" fontId="4" fillId="3" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="165" fontId="4" fillId="3" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="165" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="3" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="5" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
<xf numFmtId="166" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="164" fontId="3" fillId="4" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="4" fillId="3" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="6" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" indent="1"/></xf>
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
