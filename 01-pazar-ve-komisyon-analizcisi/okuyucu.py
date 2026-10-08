"""Ürün listesini dosyadan okur: CSV, JSON veya tarayıcıdan kaydedilmiş bir arama sayfası (HTML).

Bu araç hiçbir siteye bağlanmaz. Sayfayı kullanıcı kendi tarayıcısında açıp kaydeder; burada yalnızca
o dosya okunur.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from pazar import Urun


class OkumaHatasi(Exception):
    pass


_SUTUNLAR = {
    "ad": ("ad", "urun", "ürün", "urun adi", "ürün adı", "name", "title", "baslik", "başlık"),
    "marka": ("marka", "brand"),
    "fiyat": ("fiyat", "price", "satis fiyati", "satış fiyatı"),
    "puan": ("puan", "rating", "yildiz", "yıldız"),
    "yorum": ("yorum", "yorum sayisi", "yorum sayısı", "reviews", "degerlendirme", "değerlendirme"),
    "satici": ("satici", "satıcı", "merchant", "magaza", "mağaza"),
}


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


def _tam(deger) -> int | None:
    s = sayi(deger)
    return int(s) if s is not None else None


def csv_oku(yol: Path) -> list[Urun]:
    with open(yol, encoding="utf-8-sig", newline="") as f:
        ornek = f.read(4096)
        f.seek(0)
        ayirici = ";" if ornek.count(";") > ornek.count(",") else ","
        okur = csv.DictReader(f, delimiter=ayirici)
        if not okur.fieldnames:
            raise OkumaHatasi("CSV dosyası boş.")
        esleme = {}
        for alan, adlar in _SUTUNLAR.items():
            for baslik in okur.fieldnames:
                if baslik and baslik.strip().lower() in adlar:
                    esleme[alan] = baslik
                    break
        if "fiyat" not in esleme:
            raise OkumaHatasi("CSV'de 'fiyat' sütunu bulunamadı. Beklenen sütunlar: ad, marka, fiyat, puan, yorum.")
        urunler = []
        for satir in okur:
            fiyat = sayi(satir.get(esleme["fiyat"]))
            if fiyat is None:
                continue
            al = lambda a: (satir.get(esleme[a]) or "").strip() or None if a in esleme else None
            urunler.append(Urun(ad=al("ad") or "", fiyat=fiyat, marka=al("marka"), puan=sayi(al("puan")),
                                yorum=_tam(al("yorum")), satici=al("satici")))
    return urunler


def _sozlukten(u: dict) -> Urun | None:
    """Bir ürün sözlüğünü, alan adları kaynaktan kaynağa değişse de Urun'e çevirir."""
    fiyat_ham = u.get("price", u.get("fiyat"))
    if isinstance(fiyat_ham, dict):
        fiyat_ham = next((fiyat_ham[k] for k in ("discountedPrice", "sellingPrice", "current", "value", "originalPrice")
                          if fiyat_ham.get(k) is not None), None)
        if isinstance(fiyat_ham, dict):
            fiyat_ham = fiyat_ham.get("value")
    fiyat = sayi(fiyat_ham)
    if fiyat is None:
        return None
    marka = u.get("brand", u.get("marka"))
    if isinstance(marka, dict):
        marka = marka.get("name")
    degerlendirme = u.get("ratingScore") or u.get("rating") or {}
    if isinstance(degerlendirme, dict):
        puan = sayi(degerlendirme.get("averageRating", degerlendirme.get("average")))
        yorum = _tam(degerlendirme.get("totalCount", degerlendirme.get("totalRatingCount", degerlendirme.get("count"))))
    else:
        puan, yorum = sayi(degerlendirme), None
    puan = puan if puan is not None else sayi(u.get("puan"))
    yorum = yorum if yorum is not None else _tam(u.get("yorum", u.get("reviewCount")))
    satici = u.get("merchantName") or u.get("satici") or u.get("merchantId")
    return Urun(ad=str(u.get("name") or u.get("ad") or ""), fiyat=fiyat, marka=marka or None, puan=puan, yorum=yorum,
                satici=str(satici) if satici else None)


def json_oku(yol: Path) -> list[Urun]:
    with open(yol, encoding="utf-8") as f:
        veri = json.load(f)
    if isinstance(veri, dict):
        veri = veri.get("products") or veri.get("urunler") or []
    return [x for x in (_sozlukten(u) for u in veri if isinstance(u, dict)) if x]


def _dizi_cikar(metin: str, baslangic: int) -> str | None:
    """`baslangic` konumundaki '[' ile başlayan JSON dizisini, köşeli parantezleri sayarak çıkarır."""
    derinlik, tirnak, kacis = 0, False, False
    for i in range(baslangic, len(metin)):
        k = metin[i]
        if tirnak:
            if kacis:
                kacis = False
            elif k == "\\":
                kacis = True
            elif k == '"':
                tirnak = False
        elif k == '"':
            tirnak = True
        elif k == "[":
            derinlik += 1
        elif k == "]":
            derinlik -= 1
            if derinlik == 0:
                return metin[baslangic:i + 1]
    return None


def html_oku(yol: Path) -> list[Urun]:
    """Kaydedilmiş bir arama sayfasının içine gömülü ürün verisini okur.

    Pazaryeri sayfaları ürün listesini sayfanın içinde bir JSON bloğu olarak taşır
    ("products": [...]). Burada o blok aranır. Sayfa yapısı değişirse okuma başarısız olur ve
    kullanıcıya CSV yolu önerilir.
    """
    metin = Path(yol).read_text(encoding="utf-8", errors="ignore")
    en_iyi: list[Urun] = []
    for m in re.finditer(r'"products"\s*:\s*\[', metin):
        ham = _dizi_cikar(metin, m.end() - 1)
        if not ham:
            continue
        try:
            dizi = json.loads(ham)
        except json.JSONDecodeError:
            continue
        urunler = [x for x in (_sozlukten(u) for u in dizi if isinstance(u, dict)) if x]
        if len(urunler) > len(en_iyi):
            en_iyi = urunler
    if not en_iyi:
        raise OkumaHatasi(
            "Bu sayfada ürün listesi bulunamadı. Sayfayı 'Web sayfası, tamamı' olarak kaydettiğinizden emin olun; "
            "olmuyorsa ürünleri bir CSV dosyasına (ad, marka, fiyat, puan, yorum) yazıp onu verin."
        )
    return en_iyi


def oku(yol: str | Path) -> list[Urun]:
    yol = Path(yol)
    if not yol.exists():
        raise OkumaHatasi(f"Dosya bulunamadı: {yol}")
    uzanti = yol.suffix.lower()
    if uzanti == ".csv":
        return csv_oku(yol)
    if uzanti == ".json":
        return json_oku(yol)
    if uzanti in (".html", ".htm"):
        return html_oku(yol)
    raise OkumaHatasi("Desteklenen dosya türleri: .csv, .json, .html")
