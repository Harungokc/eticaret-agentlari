"""Ürün listesini CSV dosyasından okur. Araç hiçbir siteye bağlanmaz; listeyi kullanıcı hazırlar."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from analiz import Urun


class OkumaHatasi(Exception):
    pass


_SUTUNLAR = {
    "ad": ("ad", "urun", "ürün", "urun adi", "ürün adı", "name", "title", "baslik", "başlık"),
    "marka": ("marka", "brand"),
    "fiyat": ("fiyat", "price", "satis fiyati", "satış fiyatı"),
    "puan": ("puan", "rating", "yildiz", "yıldız"),
    "yorum": ("yorum", "yorum sayisi", "yorum sayısı", "reviews", "degerlendirme", "değerlendirme"),
    "favori": ("favori", "favori sayisi", "favori sayısı", "begeni", "beğeni"),
    "kargo": ("kargo", "kargo ucreti", "kargo ücreti", "ucretsiz kargo", "ücretsiz kargo"),
    "benim": ("benim", "benim urunum", "benim ürünüm", "kendi", "bizim"),
}
_EVET = ("evet", "e", "x", "1", "true", "var", "benim", "✓")
_UCRETSIZ = ("ücretsiz", "ucretsiz", "bedava", "evet", "var", "0", "free")
_UCRETLI = ("ücretli", "ucretli", "hayır", "hayir", "yok", "paid")


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
    return int(s) if s is not None and s >= 0 else None


def _kargo(deger) -> bool | None:
    metin = (deger or "").strip().lower()
    if not metin:
        return None
    if metin in _UCRETSIZ:
        return True
    if metin in _UCRETLI:
        return False
    tutar = sayi(metin)
    return None if tutar is None else tutar == 0


def oku(yol: str | Path) -> list[Urun]:
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
            if esleme["fiyat"] is None:
                raise OkumaHatasi("Dosyada 'fiyat' sütunu bulunamadı. İlk satır şu başlıkları içermeli: "
                                  "ad;marka;fiyat;puan;yorum (isteğe bağlı: favori;kargo;benim)")
            urunler = []
            for i, satir in enumerate(okur, 1):
                al = lambda alan: (satir.get(esleme[alan]) or "").strip() if esleme[alan] else ""  # noqa: E731
                fiyat = sayi(al("fiyat"))
                if fiyat is None or fiyat <= 0:
                    continue
                puan = sayi(al("puan"))
                urunler.append(Urun(
                    ad=al("ad") or f"Ürün {i}", fiyat=fiyat, marka=al("marka"),
                    puan=puan if puan is not None and 0 <= puan <= 5 else None,
                    yorum=_tam(al("yorum")), favori=_tam(al("favori")), kargo_ucretsiz=_kargo(al("kargo")),
                    benim=al("benim").lower() in _EVET,
                ))
    except UnicodeDecodeError:
        raise OkumaHatasi("Dosya okunamadı. CSV dosyasını UTF-8 olarak kaydedin.") from None
    if not urunler:
        raise OkumaHatasi("Dosyada fiyatı okunabilen ürün bulunamadı")
    return urunler
