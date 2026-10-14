"""Reklam raporunu ve isteğe bağlı maliyet dosyasını okur (.csv ya da .xlsx).

Pazaryerlerinin reklam raporlarında sütun adları farklıdır ve zamanla değişir. Okuyucu bilinen adları
tanır; tanıyamadığı sütunlar için eşleştirme elle verilebilir (agent.py --sutun harcama="Harcanan Tutar").
Rapor başlıktan önce birkaç açıklama satırı içeriyorsa başlık satırı ilk 15 satır içinde aranır.
Araç dosyayı yalnızca okur; hiçbir siteye bağlanmaz.
"""

from __future__ import annotations

import csv
import math
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from analiz import Maliyet, ReklamSatiri


class OkumaHatasi(Exception):
    pass


_HARF = str.maketrans("çğıöşüâîû", "cgiosuaiu")


def sade(metin) -> str:
    """Sütun adını karşılaştırılabilir hâle getirir: "7 Günlük Toplam Satış (₺)" → "7 gunluk toplam satis" """
    m = str(metin or "").replace("İ", "i").replace("I", "ı").lower().translate(_HARF)
    m = re.sub(r"\(.*?\)|\[.*?\]", " ", m)
    m = re.sub(r"[^a-z0-9]+", " ", m)
    return " ".join(m.split())


# Bilinen sütun adları (sade() hâlinde). Sıra önemlidir: ilk eşleşen alınır.
REKLAM_SUTUNLARI: dict[str, tuple[str, ...]] = {
    "urun": ("urun", "urun adi", "urun ismi", "reklami yapilan urun", "reklam verilen urun", "tanitilan urun", "advertised product",
             "product", "product name", "advertised sku", "advertised asin", "reklami yapilan sku", "reklami yapilan asin", "sku", "asin",
             "barkod", "model kodu", "stok kodu"),
    "kampanya": ("kampanya", "kampanya adi", "kampanya ismi", "campaign", "campaign name", "reklam adi", "reklam grubu",
                 "reklam grubu adi", "ad group name"),
    "terim": ("musteri arama terimi", "arama terimi", "customer search term", "search term", "anahtar kelime", "keyword",
              "hedefleme", "targeting", "kelime"),
    "harcama": ("harcama", "reklam harcamasi", "toplam harcama", "harcanan tutar", "harcanan butce", "reklam maliyeti",
                "toplam maliyet", "reklam gideri", "tuketilen butce", "spend", "cost", "amount spent", "spend amount", "maliyet"),
    "ciro": ("reklamdan gelen satis", "reklam satis tutari", "reklam cirosu", "reklamli satis", "7 gunluk toplam satis",
             "14 gunluk toplam satis", "7 day total sales", "14 day total sales", "toplam satis", "satis tutari", "satis", "satislar",
             "ciro", "gelir", "sales", "revenue", "attributed sales", "purchases conversion value", "alisveris donusum degeri",
             "donusum degeri", "tum donusum degeri", "conversion value", "total purchase value"),
    "siparis": ("7 gunluk toplam siparis", "7 gunluk toplam siparisler", "14 gunluk toplam siparis", "7 day total orders",
                "14 day total orders", "siparis", "siparisler", "siparis sayisi", "siparis adedi", "satis adedi", "satilan adet",
                "toplam siparis", "alisverisler", "donusumler", "orders", "purchases", "conversions", "7 gunluk toplam birim",
                "7 day total units", "units"),
    # Meta raporunda hem "Bağlantı Tıklamaları" hem "Tıklamalar (Tümü)" bulunur; ürüne giden tıklama önce aranır.
    "tiklama": ("baglanti tiklamalari", "link clicks", "clicks destination", "tiklama", "tiklamalar", "tiklanma", "tiklanma sayisi",
                "tiklama sayisi", "clicks"),
    # TikTok'un Türkçe arayüzünde "Görüntülemeler" gösterim demektir; video izlenmesi "Video görüntülemeleri"dir.
    "gosterim": ("gosterim", "gosterimler", "gosterim sayisi", "goruntulemeler", "goruntulenme", "goruntulenme sayisi", "impressions",
                 "impr"),
}
MALIYET_SUTUNLARI: dict[str, tuple[str, ...]] = {
    "urun": REKLAM_SUTUNLARI["urun"],
    "birim_maliyet": ("birim maliyet", "maliyet", "urun maliyeti", "alis fiyati", "alis", "uretim maliyeti", "cost", "unit cost"),
    "komisyon": ("komisyon", "komisyon orani", "komisyon yuzdesi", "commission"),
    "kargo": ("kargo", "kargo ucreti", "kargo maliyeti", "gonderim ucreti", "shipping"),
    "fiyat": ("satis fiyati", "fiyat", "price"),
}
ALAN_ADLARI = {"urun": "ürün", "kampanya": "kampanya", "terim": "arama terimi", "harcama": "harcama", "ciro": "satış tutarı",
               "siparis": "sipariş", "tiklama": "tıklama", "gosterim": "gösterim"}


def sayi(deger) -> float | None:
    """"1.234,56 TL", "1,234.56", "%12", 1234.5 → sayı; boş ya da sayı olmayan → None"""
    if isinstance(deger, (int, float)):
        return _makul(float(deger))
    if re.fullmatch(r"-?\d+(\.\d+)?[eE][-+]?\d+", str(deger).strip()):   # bilimsel gösterim: "1.2E+3"
        duz = float(str(deger).strip())
        return _makul(duz)
    metin = re.sub(r"[^\d.,-]", "", str(deger or ""))
    if not metin or metin in "-.,":
        return None
    if "," in metin and "." in metin:
        if metin.rfind(",") > metin.rfind("."):
            metin = metin.replace(".", "").replace(",", ".")
        else:
            metin = metin.replace(",", "")
    elif "," in metin:
        metin = metin.replace(",", ".") if metin.count(",") == 1 else metin.replace(",", "")
    elif metin.count(".") > 1 or re.fullmatch(r"-?\d{1,3}(\.\d{3})+", metin):
        metin = metin.replace(".", "")
    try:
        sonuc = float(metin)
    except ValueError:
        return None
    return _makul(sonuc)


def _makul(x: float) -> float | None:
    """Sonsuz ya da bir reklam raporunda olamayacak büyüklükteki (1 trilyon üstü) değer okunmaz."""
    return x if math.isfinite(x) and abs(x) <= 1e12 else None


EN_BUYUK_XML = 50 * 1024 * 1024  # açılmış hâliyle bir Excel parçası en fazla 50 MB


def _xml(z: zipfile.ZipFile, ad: str):
    """Excel içindeki bir XML parçasını güvenle okur: boyut sınırı var, DOCTYPE (dış varlık, varlık çoğaltma) reddedilir."""
    if z.getinfo(ad).file_size > EN_BUYUK_XML:
        raise OkumaHatasi("Excel dosyası çok büyük; raporu daha kısa bir dönem için indirin ya da CSV olarak kaydedin.")
    veri = z.read(ad)
    if b"<!DOCTYPE" in veri[:4096].upper() or b"<!ENTITY" in veri.upper():
        raise OkumaHatasi("Excel dosyası beklenmeyen bir yapı içeriyor ve güvenlik nedeniyle okunmadı. "
                          "Dosyayı Excel'de açıp CSV olarak kaydedip yeniden deneyin.")
    return ElementTree.fromstring(veri)


def _liste(basliklar: list[str]) -> str:
    adlar = [(b if len(b) <= 40 else b[:39] + "…") for b in basliklar if b]
    return ", ".join(adlar[:30]) + (f" … (+{len(adlar) - 30})" if len(adlar) > 30 else "")


# ------------------------------------------------------------------ dosyadan satırlar

def _xlsx_satirlari(yol: Path) -> list[list]:
    """İlk çalışma sayfasının hücrelerini okur. Ek paket gerekmez: .xlsx bir zip arşividir."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    try:
        with zipfile.ZipFile(yol) as z:
            adlar = set(z.namelist())
            ortak: list[str] = []
            if "xl/sharedStrings.xml" in adlar:
                for si in _xml(z, "xl/sharedStrings.xml").findall("m:si", ns):
                    ortak.append("".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t")))
            sayfa = "xl/worksheets/sheet1.xml"
            if "xl/workbook.xml" in adlar and "xl/_rels/workbook.xml.rels" in adlar:
                ilk = _xml(z, "xl/workbook.xml").find("m:sheets/m:sheet", ns)
                iliskiler = _xml(z, "xl/_rels/workbook.xml.rels")
                if ilk is not None:
                    kimlik = ilk.get(f"{{{ns['r']}}}id")
                    for il in iliskiler:
                        if il.get("Id") == kimlik:
                            hedef = il.get("Target", "").lstrip("/")
                            sayfa = hedef if hedef.startswith("xl/") else "xl/" + hedef
            if sayfa not in adlar:
                raise OkumaHatasi("Excel dosyasında çalışma sayfası bulunamadı")
            satirlar: list[list] = []
            for row in _xml(z, sayfa).iter(f"{{{ns['m']}}}row"):
                hucreler: dict[int, object] = {}
                for c in row.findall("m:c", ns):
                    ref = re.match(r"([A-Z]+)", c.get("r", "A"))
                    sutun = 0
                    for k in ref.group(1) if ref else "A":
                        sutun = sutun * 26 + ord(k) - 64
                    tur, v = c.get("t"), c.find("m:v", ns)
                    if tur == "s" and v is not None and v.text is not None:
                        deger: object = ortak[int(v.text)] if int(v.text) < len(ortak) else ""
                    elif tur == "inlineStr":
                        deger = "".join(t.text or "" for t in c.iter(f"{{{ns['m']}}}t"))
                    elif v is not None and v.text is not None:
                        deger = v.text if tur in ("str", "e") else (float(v.text) if re.fullmatch(r"-?[\d.]+(E-?\d+)?", v.text) else v.text)
                    else:
                        deger = ""
                    hucreler[sutun] = deger
                if hucreler:
                    en_cok = max(hucreler)
                    satirlar.append([hucreler.get(i, "") for i in range(1, en_cok + 1)])
            return satirlar
    except (zipfile.BadZipFile, ElementTree.ParseError, KeyError, ValueError):
        raise OkumaHatasi(f"Excel dosyası okunamadı: {yol.name}. Dosyayı Excel'de açıp CSV olarak kaydedip yeniden deneyin.") from None


def _csv_satirlari(yol: Path) -> list[list]:
    for kodlama in ("utf-8-sig", "cp1254"):
        try:
            metin = yol.read_text(encoding=kodlama)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise OkumaHatasi("Dosya okunamadı. CSV dosyasını UTF-8 olarak kaydedin.")
    ilk = next((s for s in metin.splitlines() if s.strip()), "")
    ayirici = max(";,\t", key=ilk.count)
    return [s for s in csv.reader(metin.splitlines(), delimiter=ayirici)]


def satirlar_oku(yol: str | Path) -> list[list]:
    yol = Path(yol)
    if not yol.exists():
        raise OkumaHatasi(f"Dosya bulunamadı: {yol}")
    uzanti = yol.suffix.lower()
    if uzanti == ".xlsx":
        return _xlsx_satirlari(yol)
    if uzanti in (".csv", ".txt", ".tsv"):
        return _csv_satirlari(yol)
    if uzanti == ".xls":
        raise OkumaHatasi("Eski Excel biçimi (.xls) okunamıyor. Dosyayı Excel'de açıp .xlsx ya da .csv olarak kaydedin.")
    raise OkumaHatasi(f"Bu araç .csv ya da .xlsx dosyası okur; verilen dosya: {yol.name}")


# ------------------------------------------------------------------ sütun eşleştirme

def _esle(basliklar: list, sozluk: dict[str, tuple[str, ...]], elle: dict[str, str]) -> dict[str, int | None]:
    sadeler = [sade(b) for b in basliklar]
    esleme: dict[str, int | None] = {}
    kullanilan: set[int] = set()
    for alan, adlar in sozluk.items():
        if alan in elle:
            hedef = sade(elle[alan])
            esleme[alan] = sadeler.index(hedef) if hedef in sadeler else None
            if esleme[alan] is None:
                raise OkumaHatasi(f"--sutun {alan}=\"{elle[alan]}\": dosyada bu adda bir sütun yok. "
                                  f"Dosyadaki sütunlar: {_liste([str(b) for b in basliklar])}")
        else:
            esleme[alan] = next((sadeler.index(a) for a in adlar if a in sadeler and sadeler.index(a) not in kullanilan), None)
        if esleme[alan] is not None:
            kullanilan.add(esleme[alan])
    return esleme


def _baslik_bul(satirlar: list[list], sozluk: dict[str, tuple[str, ...]], elle: dict[str, str]) -> int:
    """Başlık satırı: ilk 15 satır içinde en çok bilinen sütun adı içeren satır."""
    en_iyi, puan = 0, -1
    for i, s in enumerate(satirlar[:15]):
        sadeler = {sade(h) for h in s}
        p = sum(1 for adlar in sozluk.values() if any(a in sadeler for a in adlar))
        p += sum(1 for ad in elle.values() if sade(ad) in sadeler)
        if p > puan:
            en_iyi, puan = i, p
    return en_iyi


def sutunlari_goster(yol: str | Path, elle: dict[str, str] | None = None) -> tuple[list[str], dict[str, str | None]]:
    """Dosyadaki sütun adlarını ve hangisinin hangi alana eşlendiğini döndürür (eşleştirmeyi denetlemek için)."""
    satirlar = [s for s in satirlar_oku(yol) if any(str(h).strip() for h in s)]
    if not satirlar:
        raise OkumaHatasi("Dosya boş")
    elle = elle or {}
    no = _baslik_bul(satirlar, REKLAM_SUTUNLARI, elle)
    basliklar = [str(b).strip() for b in satirlar[no]]
    esleme = _esle(basliklar, REKLAM_SUTUNLARI, elle)
    return basliklar, {alan: (basliklar[i] if i is not None else None) for alan, i in esleme.items()}


def _hucre(satir: list, i: int | None):
    return satir[i] if i is not None and i < len(satir) else ""


def _metin(satir: list, i: int | None) -> str:
    d = _hucre(satir, i)
    if isinstance(d, float) and d.is_integer():
        d = int(d)
    return " ".join(str(d).split())


_TOPLAM = re.compile(r"^(genel )?toplam|^total|^grand total|^ara toplam", re.I)


def oku(yol: str | Path, elle: dict[str, str] | None = None) -> list[ReklamSatiri]:
    elle = elle or {}
    for alan in elle:
        if alan not in REKLAM_SUTUNLARI:
            raise OkumaHatasi(f"--sutun için bilinmeyen alan: {alan}. Geçerli alanlar: {', '.join(REKLAM_SUTUNLARI)}")
    satirlar = [s for s in satirlar_oku(yol) if any(str(h).strip() for h in s)]
    if not satirlar:
        raise OkumaHatasi("Dosya boş")
    no = _baslik_bul(satirlar, REKLAM_SUTUNLARI, elle)
    basliklar = [str(b).strip() for b in satirlar[no]]
    e = _esle(basliklar, REKLAM_SUTUNLARI, elle)
    if e["harcama"] is None:
        raise OkumaHatasi("Dosyada reklam harcaması sütunu tanınmadı. Dosyadaki sütunlar: "
                          + _liste(basliklar)
                          + ". Harcamanın hangi sütunda olduğunu --sutun harcama=\"Sütun adı\" ile belirtin.")
    if e["urun"] is None and e["kampanya"] is None and e["terim"] is None:
        raise OkumaHatasi("Dosyada ürün, kampanya ya da arama terimi sütunu tanınmadı. Dosyadaki sütunlar: "
                          + _liste(basliklar) + ". Örneğin --sutun urun=\"Sütun adı\" ile belirtin.")
    sonuc = []
    for s in satirlar[no + 1:]:
        etiketler = [_metin(s, e[a]) for a in ("urun", "kampanya", "terim")]
        if any(_TOPLAM.match(x) for x in etiketler if x) and not any(x and not _TOPLAM.match(x) for x in etiketler):
            continue  # raporun altındaki toplam satırı iki kez sayılmasın
        harcama = sayi(_hucre(s, e["harcama"]))
        if harcama is None and not any(etiketler):
            continue
        sonuc.append(ReklamSatiri(
            urun=etiketler[0], kampanya=etiketler[1], terim=etiketler[2], harcama=max(harcama or 0.0, 0.0),
        ))
        for alan in ("ciro", "siparis", "tiklama", "gosterim"):
            if e[alan] is not None:
                # sütun var ama hücre boşsa sıfır; eksi değer (düzeltme satırı vb.) sıfır sayılır
                setattr(sonuc[-1], alan, max(sayi(_hucre(s, e[alan])) or 0.0, 0.0))
    if not sonuc:
        raise OkumaHatasi("Dosyada okunabilen reklam satırı bulunamadı")
    return sonuc


def maliyet_oku(yol: str | Path) -> list[Maliyet]:
    satirlar = [s for s in satirlar_oku(yol) if any(str(h).strip() for h in s)]
    if not satirlar:
        raise OkumaHatasi("Maliyet dosyası boş")
    no = _baslik_bul(satirlar, MALIYET_SUTUNLARI, {})
    basliklar = [str(b).strip() for b in satirlar[no]]
    e = _esle(basliklar, MALIYET_SUTUNLARI, {})
    if e["urun"] is None or e["birim_maliyet"] is None:
        raise OkumaHatasi("Maliyet dosyasında 'ürün' ve 'maliyet' sütunları olmalı (isteğe bağlı: komisyon, kargo, satış fiyatı). "
                          "Dosyadaki sütunlar: " + _liste(basliklar))
    sonuc = []
    for s in satirlar[no + 1:]:
        ad = _metin(s, e["urun"])
        maliyet = sayi(_hucre(s, e["birim_maliyet"]))
        if not ad or maliyet is None:
            continue
        komisyon = sayi(_hucre(s, e["komisyon"])) or 0.0
        if komisyon > 1:          # "20" ya da "%20" → 0,20; "0,2" olduğu gibi kalır
            komisyon /= 100
        if not 0 <= komisyon < 1:
            raise OkumaHatasi(f"Maliyet dosyasında '{ad}' için komisyon oranı anlaşılmadı; %0 ile %100 arasında olmalı")
        fiyat = sayi(_hucre(s, e["fiyat"])) if e["fiyat"] is not None else None
        sonuc.append(Maliyet(urun=ad, birim_maliyet=max(maliyet, 0.0), komisyon=komisyon,
                             kargo=max(sayi(_hucre(s, e["kargo"])) or 0.0, 0.0), fiyat=fiyat if fiyat and fiyat > 0 else None))
    if not sonuc:
        raise OkumaHatasi("Maliyet dosyasında okunabilen satır bulunamadı")
    return sonuc
