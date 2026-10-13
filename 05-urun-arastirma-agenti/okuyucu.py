"""Aday ürün listesini CSV dosyasından okur. Araç hiçbir siteye bağlanmaz; listeyi asistan ya da kullanıcı hazırlar."""

from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path

from analiz import Aday, AyTarihi, katla, yuvarla


class OkumaHatasi(Exception):
    pass


BASLIKLAR = ("ad;kategori;marka;orijinal_ad;cince_ad;urun_link;gorsel;yurtdisi_fiyat;tedarik_fiyat;tedarik_moq;tedarikci;tedarik_link;ulke;kaynak;kaynak_tarihi;satis_sirasi;yorum;son_satis;son_satis_gun;"
             "toplam_satis;satis_degisim;veri_tarihi;izlenme;trend;tr_satici;tr_fiyat;tr_kontrol;tr_kaynak;maliyet;satis_fiyati;komisyon;kargo;not")

_SUTUNLAR = {
    "ad": ("ad", "urun", "ürün", "urun adi", "ürün adı", "name", "title"),
    "kategori": ("kategori", "category", "tur", "tür"),
    "marka": ("marka", "brand"),
    "orijinal_ad": ("orijinal_ad", "orijinal ad", "ilan adi", "ilan adı", "listedeki ad", "original_name"),
    "urun_link": ("urun_link", "urun link", "ürün linki", "urun baglantisi", "ürün bağlantısı", "urun sayfasi", "product_url"),
    "cince_ad": ("cince_ad", "çince ad", "cince ad", "chinese_name", "中文名"),
    "tedarik_fiyat": ("tedarik_fiyat", "tedarik fiyat", "tedarik fiyatı", "toptan fiyat", "fabrika fiyati", "fabrika fiyatı"),
    "tedarik_moq": ("tedarik_moq", "moq", "en az siparis", "en az sipariş", "asgari siparis", "asgari sipariş"),
    "tedarikci": ("tedarikci", "tedarikçi", "supplier", "uretici", "üretici"),
    "tedarik_link": ("tedarik_link", "tedarik link", "tedarikci link", "tedarikçi linki", "supplier_url"),
    "gorsel": ("gorsel", "görsel", "resim", "fotograf", "fotoğraf", "image", "image_url"),
    "satis_degisim": ("satis_degisim", "satis degisim", "satış değişimi", "aylik degisim", "aylık değişim", "mom", "buyume", "büyüme"),
    "yurtdisi_fiyat": ("yurtdisi_fiyat", "yurtdışı fiyat", "yurt dışı fiyat", "yurtdisi fiyat", "kaynak fiyat"),
    "ulke": ("ulke", "ülke", "pazar", "country"),
    "kaynak": ("kaynak", "kaynaklar", "kaynak link", "link", "linkler", "baglanti", "bağlantı", "url", "source"),
    "kaynak_tarihi": ("kaynak_tarihi", "kaynak tarihi", "kaynak tarihleri", "yayin tarihi", "yayın tarihi"),
    "satis_sirasi": ("satis_sirasi", "satis sirasi", "satış sırası", "sira", "sıra", "rank"),
    "yorum": ("yorum", "yorum sayisi", "yorum sayısı", "reviews"),
    "son_satis": ("son_satis", "son satis", "son satış", "son donem satis", "son dönem satış"),
    "son_satis_gun": ("son_satis_gun", "son satis gun", "son satış gün", "donem", "dönem", "gun", "gün"),
    "toplam_satis": ("toplam_satis", "toplam satis", "toplam satış", "toplam adet"),
    "veri_tarihi": ("veri_tarihi", "veri tarihi", "tarih"),
    "izlenme": ("izlenme", "izlenme sayisi", "izlenme sayısı", "goruntulenme", "görüntülenme", "views"),
    "trend": ("trend", "yon", "yön", "google trends"),
    "tr_satici": ("tr_satici", "tr satici", "tr satıcı", "tr_ilan", "tr ilan", "turkiye satici", "türkiye satıcı", "satici sayisi", "satıcı sayısı"),
    "tr_fiyat": ("tr_fiyat", "tr fiyat", "turkiye fiyat", "türkiye fiyat", "turkiye fiyati", "türkiye fiyatı"),
    "tr_kontrol": ("tr_kontrol", "tr kontrol", "kim bakti", "kim baktı"),
    "tr_kaynak": ("tr_kaynak", "tr kaynak", "tr link", "turkiye kaynak", "türkiye kaynak"),
    "maliyet": ("maliyet", "toplam maliyet", "alis", "alış", "cost"),
    "satis_fiyati": ("satis_fiyati", "satis fiyati", "satış fiyatı", "fiyat", "price"),
    "komisyon": ("komisyon", "komisyon orani", "komisyon oranı"),
    "kargo": ("kargo", "kargo ucreti", "kargo ücreti"),
    "aciklama": ("not", "notlar", "aciklama", "açıklama"),
}
_AYLAR = {ad: no for no, adlar in enumerate((
    ("ocak", "oca", "january", "jan"), ("subat", "sub", "february", "feb"), ("mart", "mar", "march"),
    ("nisan", "nis", "april", "apr"), ("mayis", "may"), ("haziran", "haz", "june", "jun"),
    ("temmuz", "tem", "july", "jul"), ("agustos", "agu", "august", "aug"), ("eylul", "eyl", "september", "sep", "sept"),
    ("ekim", "eki", "october", "oct"), ("kasim", "kas", "november", "nov"), ("aralik", "ara", "december", "dec")), 1) for ad in adlar}
_CARPANLAR = {"k": 1e3, "b": 1e3, "bin": 1e3, "m": 1e6, "mn": 1e6, "milyon": 1e6, "mr": 1e9, "milyar": 1e9}


def sayi(deger) -> float | None:
    """"1.299,90 TL", "1299.9", 1299.9 → 1299.9; anlaşılmazsa None."""
    if deger is None or isinstance(deger, bool):
        return None
    if isinstance(deger, (int, float)):
        return float(deger)
    metin = re.sub(r"[^\d.,-]", "", str(deger))
    if not metin:
        return None
    if "," in metin:
        metin = metin.replace(".", "").replace(",", ".")
    elif metin.count(".") > 1 or re.fullmatch(r"\d{1,3}(\.\d{3})+", metin):
        metin = metin.replace(".", "")  # 1.299 → binlik ayırıcı
    try:
        return float(metin)
    except ValueError:
        return None


def adet(deger) -> int | None:
    """"12500", "12.500", "2,4 milyon", "850 bin", "1.2M" → tam sayı; anlaşılmazsa ya da eksi ise None."""
    metin = str(deger or "").strip().lower()
    if not metin:
        return None
    es = re.fullmatch(r"([\d.,]+)\s*([a-zçğıöşü]+)\.?", metin)
    if es and es.group(2) in _CARPANLAR:
        govde = es.group(1)
        # Kısaltmalı yazımda tek nokta ondalıktır: 1.2M → 1,2 milyon
        s = float(govde) if re.fullmatch(r"\d+\.\d{1,2}", govde) else sayi(govde)
        return int(round(s * _CARPANLAR[es.group(2)])) if s is not None and s >= 0 else None
    if re.search(r"[a-zçğıöşü]", metin):
        return None
    s = sayi(metin)
    return int(s) if s is not None and s >= 0 else None


def tarih(deger) -> date | None:
    """"2026-10-01", "2026-10", "01.10.2026", "1 Ekim 2026", "Ekim 2026", "Oct 2, 2026" → tarih; anlaşılmazsa None.

    Günü yazılmamış tarih ayın ilk günü sayılır. "10/02/2026" gibi gün ve ayı karışabilen yazımlar kabul edilmez.
    """
    metin = str(deger or "").strip()
    try:
        if es := re.fullmatch(r"(\d{4})-(\d{1,2})(?:-(\d{1,2}))?", metin):
            return (date if es.group(3) else AyTarihi)(int(es.group(1)), int(es.group(2)), int(es.group(3) or 1))
        if es := re.fullmatch(r"(?:(\d{1,2})\.)?(\d{1,2})\.(\d{4})", metin):
            return (date if es.group(1) else AyTarihi)(int(es.group(3)), int(es.group(2)), int(es.group(1) or 1))
        parcalar = re.split(r"[\s,.]+", katla(metin).strip(" ,."))
        aylar = [_AYLAR[p] for p in parcalar if p in _AYLAR]
        yillar = [int(p) for p in parcalar if re.fullmatch(r"\d{4}", p)]
        gunler = [int(p) for p in parcalar if re.fullmatch(r"\d{1,2}", p)]
        if len(aylar) == 1 and len(yillar) == 1 and len(gunler) <= 1 and len(parcalar) == 2 + len(gunler):
            return (date if gunler else AyTarihi)(yillar[0], aylar[0], gunler[0] if gunler else 1)
    except ValueError:
        pass
    return None


def trend(deger) -> str | None:
    """Arama ilgisinin yönü: "yükseliyor", "düz" ya da "düşüyor"; anlaşılmazsa None."""
    metin = katla(str(deger or "")).strip()
    if metin.startswith(("yuksel", "art", "rising", "breakout")):
        return "yükseliyor"
    if metin.startswith(("duz", "sabit", "yatay", "flat", "stable")):
        return "düz"
    if metin.startswith(("dus", "azal", "falling", "declin")):
        return "düşüyor"
    return None


def degisim(deger) -> float | None:
    """Yüzde değişim: "33.3", "%33,3", "▲ 33.3%", "+12", "▼ 8%", "-8" → 33.3, 33.3, 33.3, 12.0, -8.0, -8.0."""
    metin = str(deger or "").strip()
    es = re.search(r"\d+(?:[.,]\d+)?", metin)
    if not es or re.search(r"[a-zçğıöşü]", metin.lower()):
        return None
    s = float(es.group().replace(",", "."))
    return -s if re.search(r"[▼↓−-]", metin[:es.start()] + metin[es.end():]) else s


def gun(deger) -> int | None:
    """Satış adedinin ait olduğu dönem, gün olarak: "7", "7 gün", "1 hafta", "ay" → 7, 7, 7, 30."""
    metin = katla(str(deger or "")).strip()
    es = re.match(r"\d+", metin)
    kat = 7 if "hafta" in metin or "week" in metin else 30 if re.search(r"\bay\b|month", metin) else 1 if es else None
    if kat is None:
        return None
    n = int(es.group()) * kat if es else kat
    return n if 1 <= n <= 366 else None


def sira(deger) -> int | None:
    """Satış sırası; aylık ortalama olarak verilen ondalıklı sıra en yakın tam sayıya yuvarlanır ("5.8" → 6)."""
    s = sayi(deger) if not re.search(r"[a-zçğıöşü]", str(deger or "").lower()) else None
    return max(1, int(yuvarla(s))) if s is not None and s > 0 else None


def _para(deger) -> float | None:
    s = sayi(deger)
    return s if s is not None and s >= 0 else None


def _kaynaklar(deger: str) -> list[str]:
    return [k for k in re.split(r"[\s|]+", deger.strip()) if "." in k]


def _kaynak_tarihleri(deger: str, kac: int) -> list[date | None]:
    """Kaynaklarla aynı sırada, boşlukla ya da "|" ile ayrılmış tarihler; bilinmeyen için "-" yazılır."""
    parcalar = [p.strip() for p in (deger.split("|") if "|" in deger else deger.split())]
    return ([tarih(p) for p in parcalar] + [None] * kac)[:kac]


def _kontrol(deger: str, sayi_var: bool) -> str:
    if not sayi_var:
        return ""
    return "satıcı" if katla(deger).strip().startswith(("satici", "ben", "kendi", "elle", "kullanici")) else "asistan"


def oku(yol: str | Path) -> list[Aday]:
    yol = Path(yol)
    if not yol.exists():
        raise OkumaHatasi(f"Dosya bulunamadı: {yol}")
    if yol.suffix.lower() != ".csv":
        raise OkumaHatasi(f"Bu araç ürün listesini .csv dosyasından okur; verilen dosya: {yol.name}")
    try:
        with open(yol, encoding="utf-8-sig", newline="") as f:
            ornek = f.read(4096)
            f.seek(0)
            ayirici = ";" if ornek.count(";") > ornek.count(",") else ","
            okur = csv.DictReader(f, delimiter=ayirici)
            basliklar = {(b or "").strip().lower(): b for b in (okur.fieldnames or [])}
            esleme = {alan: next((basliklar[a] for a in adlar if a in basliklar), None) for alan, adlar in _SUTUNLAR.items()}
            if esleme["ad"] is None:
                raise OkumaHatasi("Dosyada 'ad' sütunu bulunamadı. İlk satır şu başlıkları içermeli: " + BASLIKLAR)
            adaylar = []
            for satir in okur:
                if None in satir:
                    raise OkumaHatasi(f"{okur.line_num}. satırda başlıktakinden fazla sütun var. Bir hücrenin içinde "
                                      f"'{ayirici}' geçiyorsa o hücreyi çift tırnak içine alın.")
                al = lambda alan: (satir.get(esleme[alan]) or "").strip() if esleme[alan] else ""  # noqa: E731
                if not al("ad"):
                    continue
                komisyon = _para(al("komisyon"))
                kaynaklar, tr_satici = _kaynaklar(al("kaynak")), adet(al("tr_satici"))
                adaylar.append(Aday(
                    ad=al("ad"), kategori=al("kategori"), marka=al("marka"), orijinal_ad=al("orijinal_ad"),
                    urun_linkleri=_kaynaklar(al("urun_link")), gorsel=al("gorsel").split()[0] if al("gorsel") else "", cince_ad=al("cince_ad"),
                    tedarik_fiyat=al("tedarik_fiyat"), tedarik_moq=al("tedarik_moq"), tedarikci=al("tedarikci"), tedarik_linkleri=_kaynaklar(al("tedarik_link")), yurtdisi_fiyat=al("yurtdisi_fiyat"), ulke=al("ulke"), kaynaklar=kaynaklar,
                    kaynak_tarihleri=_kaynak_tarihleri(al("kaynak_tarihi"), len(kaynaklar)),
                    satis_sirasi=sira(al("satis_sirasi")), yorum=adet(al("yorum")), son_satis=adet(al("son_satis")),
                    son_satis_gun=gun(al("son_satis_gun")), toplam_satis=adet(al("toplam_satis")), satis_degisim=degisim(al("satis_degisim")),
                    veri_tarihi=tarih(al("veri_tarihi")), izlenme=adet(al("izlenme")), trend=trend(al("trend")),
                    tr_satici=tr_satici, tr_fiyat=_para(al("tr_fiyat")), tr_kontrol=_kontrol(al("tr_kontrol"), tr_satici is not None),
                    tr_kaynaklar=_kaynaklar(al("tr_kaynak")), maliyet=_para(al("maliyet")),
                    satis_fiyati=_para(al("satis_fiyati")),
                    komisyon=komisyon if komisyon is not None and komisyon < 100 else None,
                    kargo=_para(al("kargo")), aciklama=al("aciklama"),
                ))
    except UnicodeDecodeError:
        raise OkumaHatasi("Dosya okunamadı. CSV dosyasını UTF-8 olarak kaydedin.") from None
    if not adaylar:
        raise OkumaHatasi("Dosyada adı yazılı ürün bulunamadı")
    return adaylar
