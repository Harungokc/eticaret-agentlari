"""Pazar analizi — bir ürün listesinden pazarın fotoğrafını çıkarır.

Girdi, bir arama veya kategori sayfasındaki ürünlerin listesidir (ad, marka, fiyat, puan, yorum
sayısı). Çıktıdaki her sayı bu listeden sayılarak ya da hesaplanarak bulunur; satış adedi veya ciro
tahmini YAPILMAZ, çünkü sayfada bu bilgi yoktur. Yorum sayısı yalnızca ilginin dolaylı göstergesidir.
"""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Urun:
    ad: str
    fiyat: float
    marka: str | None = None
    puan: float | None = None
    yorum: int | None = None
    satici: str | None = None


@dataclass
class Bant:
    alt: float
    ust: float
    urun_sayisi: int
    ortalama_yorum: float | None


@dataclass
class PazarRaporu:
    urun_sayisi: int
    marka_sayisi: int
    satici_sayisi: int | None
    fiyat_min: float
    fiyat_ceyrek1: float
    fiyat_medyan: float
    fiyat_ceyrek3: float
    fiyat_max: float
    fiyat_ortalama: float
    bantlar: list[Bant]
    markalar: list[tuple[str, int, float]]  # (marka, ürün sayısı, ürünlerdeki payı %)
    puan_medyan: float | None
    yorum_medyan: float | None
    yorum_toplam: int | None
    ilk10_yorum_payi: float | None  # en çok yorumlu 10 ürünün toplam yorumdaki payı, %
    yogunluk: str | None  # "yoğunlaşmış" | "orta" | "dağınık"
    bosluk: Bant | None
    uyarilar: list[str] = field(default_factory=list)


EN_AZ_URUN = 8


def _ceyrekler(degerler: list[float]) -> tuple[float, float, float]:
    c1, c2, c3 = statistics.quantiles(degerler, n=4, method="inclusive")
    return c1, c2, c3


def _yuzdelik(sirali: list[float], p: float) -> float:
    i = (len(sirali) - 1) * p
    alt, ust = int(i), min(int(i) + 1, len(sirali) - 1)
    return sirali[alt] + (sirali[ust] - sirali[alt]) * (i - alt)


def _bantlar(urunler: list[Urun], adet: int = 4) -> list[Bant]:
    """Fiyat aralığını eşit genişlikte bantlara böler.

    Uç fiyatlar (en ucuz ve en pahalı %5) bant sınırlarını bozmasın diye sınırlar 5. ve 95.
    yüzdeliklerden kurulur; uçtaki ürünler ilk ve son banda sayılır.
    """
    fiyatlar = sorted(u.fiyat for u in urunler)
    alt, ust = _yuzdelik(fiyatlar, 0.05), _yuzdelik(fiyatlar, 0.95)
    if ust <= alt:
        return [Bant(fiyatlar[0], fiyatlar[-1], len(urunler), _ort_yorum(urunler))]
    genislik = (ust - alt) / adet
    sinirlar = [round(alt + i * genislik) for i in range(adet + 1)]
    sinirlar[0], sinirlar[-1] = fiyatlar[0], fiyatlar[-1]
    bantlar = []
    for i in range(adet):
        a, b = sinirlar[i], sinirlar[i + 1]
        son = i == adet - 1
        icinde = [u for u in urunler if a <= u.fiyat < b or (son and u.fiyat == b)]
        bantlar.append(Bant(a, b, len(icinde), _ort_yorum(icinde)))
    return bantlar


def _ort_yorum(urunler: list[Urun]) -> float | None:
    y = [u.yorum for u in urunler if u.yorum is not None]
    return round(statistics.mean(y), 1) if y else None


def analiz_et(urunler: list[Urun]) -> PazarRaporu:
    urunler = [u for u in urunler if u.fiyat and u.fiyat > 0]
    if len(urunler) < EN_AZ_URUN:
        raise ValueError(f"Pazar analizi için en az {EN_AZ_URUN} ürün gerekir; {len(urunler)} ürün okundu.")

    uyarilar: list[str] = []
    fiyatlar = [u.fiyat for u in urunler]
    c1, medyan, c3 = _ceyrekler(fiyatlar)

    markali = [u.marka.strip() for u in urunler if u.marka and u.marka.strip()]
    sayim = Counter(markali)
    markalar = [(m, n, round(100 * n / len(urunler), 1)) for m, n in sayim.most_common(5)]
    if len(markali) < len(urunler):
        uyarilar.append(f"{len(urunler) - len(markali)} üründe marka bilgisi yok; marka payları kalan ürünlerden hesaplandı.")

    saticilar = {u.satici for u in urunler if u.satici}
    puanlar = [u.puan for u in urunler if u.puan]
    yorumlar = sorted((u.yorum for u in urunler if u.yorum is not None), reverse=True)

    ilk10 = yogunluk = None
    if len(yorumlar) >= 20 and sum(yorumlar) > 0:
        ilk10 = round(100 * sum(yorumlar[:10]) / sum(yorumlar), 1)
        # Kaba bir sınıflama: eşit dağılımda ilk 10 ürünün payı 10/N olurdu.
        yogunluk = "yoğunlaşmış" if ilk10 >= 60 else "orta" if ilk10 >= 35 else "dağınık"
    elif yorumlar:
        uyarilar.append("Rekabet yoğunluğu için yorum bilgisi olan en az 20 ürün gerekir; hesaplanmadı.")
    else:
        uyarilar.append("Listede yorum sayısı yok; ilgi ve rekabet göstergeleri hesaplanmadı.")

    bantlar = _bantlar(urunler)
    bosluk = None
    yorum_medyan = statistics.median(yorumlar) if yorumlar else None
    if yorum_medyan is not None and len(bantlar) > 1:
        ortalama_adet = len(urunler) / len(bantlar)
        adaylar = [b for b in bantlar
                   if 0 < b.urun_sayisi < ortalama_adet * 0.6 and (b.ortalama_yorum or 0) >= yorum_medyan]
        if adaylar:
            bosluk = min(adaylar, key=lambda b: b.urun_sayisi)

    return PazarRaporu(
        urun_sayisi=len(urunler),
        marka_sayisi=len(sayim),
        satici_sayisi=len(saticilar) or None,
        fiyat_min=min(fiyatlar), fiyat_ceyrek1=round(c1, 2), fiyat_medyan=round(medyan, 2),
        fiyat_ceyrek3=round(c3, 2), fiyat_max=max(fiyatlar), fiyat_ortalama=round(statistics.mean(fiyatlar), 2),
        bantlar=bantlar, markalar=markalar,
        puan_medyan=round(statistics.median(puanlar), 2) if puanlar else None,
        yorum_medyan=yorum_medyan, yorum_toplam=sum(yorumlar) if yorumlar else None,
        ilk10_yorum_payi=ilk10, yogunluk=yogunluk, bosluk=bosluk, uyarilar=uyarilar,
    )
