"""Sipariş listesini CSV dosyasından okur. Yalnızca il, ilçe, tutar, ürün, sipariş no ve durum sütunları
alınır; müşteri adı, telefon ve adres sütunları dosyada olsa bile okunmaz."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from analiz import Siparis, il_bul


class OkumaHatasi(Exception):
    pass


_SUTUNLAR = {
    "il": ("il", "şehir", "sehir", "teslimat ili", "teslimat şehri", "il adı", "city", "province", "fatura ili"),
    "ilce": ("ilçe", "ilce", "teslimat ilçesi", "ilçe adı", "district", "semt"),
    "tutar": ("tutar", "toplam tutar", "sipariş tutarı", "satış tutarı", "faturalanacak tutar", "fatura tutarı", "toplam", "fiyat",
              "amount", "total"),
    "urun": ("ürün", "urun", "ürün adı", "urun adi", "product", "ürün ismi"),
    "no": ("sipariş no", "siparis no", "sipariş numarası", "siparis numarasi", "order", "order id", "sipariş id", "paket no"),
    "durum": ("durum", "sipariş durumu", "siparis durumu", "status", "sipariş statüsü"),
}


def sayi(deger) -> float | None:
    metin = re.sub(r"[^\d.,-]", "", str(deger or ""))
    if not metin:
        return None
    if "," in metin:
        metin = metin.replace(".", "").replace(",", ".")
    elif metin.count(".") > 1 or re.fullmatch(r"\d{1,3}(\.\d{3})+", metin):
        metin = metin.replace(".", "")
    try:
        return float(metin)
    except ValueError:
        return None


def oku(yol: str | Path) -> list[Siparis]:
    yol = Path(yol)
    if not yol.exists():
        raise OkumaHatasi(f"Dosya bulunamadı: {yol}")
    if yol.suffix.lower() != ".csv":
        raise OkumaHatasi(f"Bu araç sipariş listesini .csv dosyasından okur; verilen dosya: {yol.name}")
    try:
        with open(yol, encoding="utf-8-sig", newline="") as f:
            ornek = f.read(4096)
            f.seek(0)
            ilk = ornek.splitlines()[0] if ornek.splitlines() else ""
            ayirici = max(";,\t", key=ilk.count)
            okur = csv.DictReader(f, delimiter=ayirici)
            basliklar = {(b or "").strip().replace("İ", "i").replace("I", "ı").lower(): b for b in (okur.fieldnames or [])}
            esleme = {alan: next((basliklar[a] for a in adlar if a in basliklar), None) for alan, adlar in _SUTUNLAR.items()}
            if esleme["il"] is None:
                raise OkumaHatasi("Dosyada 'il' sütunu bulunamadı. İlk satır şu başlıkları içermeli: il;ilçe;tutar "
                                  "(isteğe bağlı: ürün;sipariş no;durum)")
            siparisler = []
            for satir in okur:
                al = lambda alan: (satir.get(esleme[alan]) or "").strip() if esleme[alan] else ""  # noqa: E731
                il_ham = al("il")
                if not il_ham and not al("ilce") and not al("tutar"):
                    continue
                durum = al("durum").replace("İ", "i").replace("I", "ı").lower()
                tutar = sayi(al("tutar"))
                siparisler.append(Siparis(
                    il=il_bul(il_ham), il_ham=il_ham, ilce=al("ilce"), tutar=tutar if tutar is not None and tutar >= 0 else None,
                    urun=al("urun"), no=al("no"), iade="iade" in durum, iptal="iptal" in durum,
                ))
    except UnicodeDecodeError:
        raise OkumaHatasi("Dosya okunamadı. CSV dosyasını UTF-8 olarak kaydedin.") from None
    if not siparisler:
        raise OkumaHatasi("Dosyada okunabilen sipariş bulunamadı")
    return siparisler
