"""Ürün listesinden üç hesap: pazar ortalamaları, fiyat konumu ve rakip karşılaştırması.

Araç hiçbir siteye bağlanmaz; listeyi kullanıcı verir. Buradaki her rakam o listeden hesaplanır,
tahmin ya da dışarıdan veri eklenmez.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, median

EN_AZ_URUN = 5  # bundan az ürünle ortalama ve konum anlamlı değil
EN_AZ_YORUMLU = 8  # ilgi gören aralık için yorum sayısı bilinen en az ürün
YAKIN_ORAN = 0.10  # "benzer fiyatlı" sayılan aralık: fiyatın ±%10'u


@dataclass
class Urun:
    ad: str
    fiyat: float
    marka: str = ""
    puan: float | None = None
    yorum: int | None = None
    favori: int | None = None
    kargo_ucretsiz: bool | None = None
    benim: bool = False


def yuzdelik(sirali: list[float], p: float) -> float:
    """Excel'in QUARTILE/PERCENTILE işleviyle aynı yöntem (uçlar dahil, doğrusal ara değer)."""
    if len(sirali) == 1:
        return sirali[0]
    yer = p * (len(sirali) - 1)
    alt = int(yer)
    ust = min(alt + 1, len(sirali) - 1)
    return sirali[alt] + (sirali[ust] - sirali[alt]) * (yer - alt)


def ayir(urunler: list[Urun]) -> tuple[Urun | None, list[Urun]]:
    """Kullanıcının ürününü (varsa) pazardaki diğer ürünlerden ayırır."""
    gecerli = [u for u in urunler if u.fiyat and u.fiyat > 0]
    benimkiler = [u for u in gecerli if u.benim]
    if len(benimkiler) > 1:
        raise ValueError("Listede birden fazla ürün 'benim' olarak işaretli; yalnızca kendi ürününüzü işaretleyin")
    return (benimkiler[0] if benimkiler else None), [u for u in gecerli if not u.benim]


# ---------------------------------------------------------------- 1) ortalamalar


@dataclass
class Olcu:
    """Bir sütunun özeti; `adet`, o değeri bilinen ürün sayısıdır."""
    adet: int
    ortalama: float | None = None
    ortanca: float | None = None
    en_az: float | None = None
    en_cok: float | None = None
    toplam: float | None = None


def _olcu(degerler: list[float]) -> Olcu:
    if not degerler:
        return Olcu(0)
    return Olcu(len(degerler), mean(degerler), median(degerler), min(degerler), max(degerler), sum(degerler))


@dataclass
class Ozet:
    urun_sayisi: int
    fiyat: Olcu
    alt_ceyrek: float
    ust_ceyrek: float
    puan: Olcu
    yorum: Olcu
    favori: Olcu
    yorum_agirlikli_fiyat: float | None  # yorumu çok olan ürünlerin fiyatına daha çok ağırlık verir
    ucretsiz_kargo_orani: float | None  # 0-100; kargo bilgisi olan ürünler içinde
    kargo_bilinen: int
    uyarilar: list[str] = field(default_factory=list)


def ozet(pazar: list[Urun]) -> Ozet:
    if len(pazar) < EN_AZ_URUN:
        raise ValueError(f"Bu analiz için en az {EN_AZ_URUN} ürün gerekir; listede fiyatı okunabilen {len(pazar)} ürün var")
    fiyatlar = sorted(u.fiyat for u in pazar)
    yorumlu = [u for u in pazar if u.yorum is not None]
    toplam_yorum = sum(u.yorum for u in yorumlu)
    kargolu = [u for u in pazar if u.kargo_ucretsiz is not None]
    r = Ozet(
        urun_sayisi=len(pazar),
        fiyat=_olcu(fiyatlar),
        alt_ceyrek=yuzdelik(fiyatlar, 0.25),
        ust_ceyrek=yuzdelik(fiyatlar, 0.75),
        puan=_olcu([u.puan for u in pazar if u.puan is not None]),
        yorum=_olcu([float(u.yorum) for u in yorumlu]),
        favori=_olcu([float(u.favori) for u in pazar if u.favori is not None]),
        yorum_agirlikli_fiyat=(sum(u.fiyat * u.yorum for u in yorumlu) / toplam_yorum) if toplam_yorum > 0 else None,
        ucretsiz_kargo_orani=(100 * sum(u.kargo_ucretsiz for u in kargolu) / len(kargolu)) if kargolu else None,
        kargo_bilinen=len(kargolu),
    )
    if len(pazar) < 20:
        r.uyarilar.append(f"Liste {len(pazar)} üründen oluşuyor; 20 ve üzeri ürünle ortalamalar daha güvenilir olur.")
    if r.fiyat.en_cok > 10 * r.fiyat.ortanca:
        r.uyarilar.append("Listede ortancanın 10 katından pahalı ürün var; farklı türde bir ürün karışmış olabilir. "
                          "Ortalama fiyat yerine ortanca fiyata bakın.")
    return r


# ---------------------------------------------------------------- 2) fiyat konumu


@dataclass
class Aralik:
    alt: float
    ust: float
    urun_sayisi: int
    ortanca_yorum: float | None


@dataclass
class Konum:
    fiyat: float
    urun_sayisi: int
    daha_ucuz: int
    ayni: int
    daha_pahali: int
    yuzdelik: float  # 0 = en ucuz, 100 = en pahalı
    dilim: str
    ortanca: float
    ortancadan_fark: float  # yüzde; eksi ise ortancadan ucuz
    ana_aralik: tuple[float, float]  # alt ve üst çeyrek: ürünlerin ortadaki yarısı
    ana_aralikta: bool
    yakin_sayisi: int  # fiyatın ±%10'undaki ürün sayısı
    yakin_ortanca_puan: float | None
    yakin_ortanca_yorum: float | None
    dilimler: list[Aralik]
    ilgi_goren: Aralik | None  # ortanca yorumu en yüksek fiyat dilimi
    uyarilar: list[str] = field(default_factory=list)


def _dilimler(pazar: list[Urun]) -> list[Aralik]:
    """Ürünleri fiyata göre sıralayıp eşit sayıda dört dilime böler."""
    sirali = sorted(pazar, key=lambda u: u.fiyat)
    n = len(sirali)
    sonuc = []
    for i in range(4):
        parca = sirali[i * n // 4:(i + 1) * n // 4]
        if not parca:
            continue
        yorumlar = [u.yorum for u in parca if u.yorum is not None]
        sonuc.append(Aralik(parca[0].fiyat, parca[-1].fiyat, len(parca), median(yorumlar) if yorumlar else None))
    return sonuc


def konum(pazar: list[Urun], fiyat: float) -> Konum:
    if fiyat <= 0:
        raise ValueError("Fiyat sıfırdan büyük olmalı")
    if len(pazar) < EN_AZ_URUN:
        raise ValueError(f"Bu analiz için en az {EN_AZ_URUN} ürün gerekir; listede fiyatı okunabilen {len(pazar)} ürün var")
    fiyatlar = sorted(u.fiyat for u in pazar)
    n = len(fiyatlar)
    ucuz = sum(f < fiyat for f in fiyatlar)
    ayni = sum(f == fiyat for f in fiyatlar)
    q1, q2, q3 = (yuzdelik(fiyatlar, p) for p in (0.25, 0.5, 0.75))
    if fiyat < q1:
        dilim = "en ucuz çeyrekte"
    elif fiyat < q2:
        dilim = "ortancanın altında"
    elif fiyat <= q3:
        dilim = "ortancanın üstünde" if fiyat > q2 else "tam ortancada"
    else:
        dilim = "en pahalı çeyrekte"
    yakin = [u for u in pazar if abs(u.fiyat - fiyat) <= fiyat * YAKIN_ORAN]
    yakin_puan = [u.puan for u in yakin if u.puan is not None]
    yakin_yorum = [u.yorum for u in yakin if u.yorum is not None]
    dilimler = _dilimler(pazar)
    ilgi = None
    if sum(u.yorum is not None for u in pazar) >= EN_AZ_YORUMLU:
        adaylar = [d for d in dilimler if d.ortanca_yorum is not None]
        if adaylar:
            ilgi = max(adaylar, key=lambda d: d.ortanca_yorum)
    r = Konum(
        fiyat=fiyat, urun_sayisi=n, daha_ucuz=ucuz, ayni=ayni, daha_pahali=n - ucuz - ayni,
        yuzdelik=100 * (ucuz + ayni / 2) / n, dilim=dilim, ortanca=q2, ortancadan_fark=100 * (fiyat - q2) / q2,
        ana_aralik=(q1, q3), ana_aralikta=q1 <= fiyat <= q3,
        yakin_sayisi=len(yakin), yakin_ortanca_puan=median(yakin_puan) if yakin_puan else None,
        yakin_ortanca_yorum=median(yakin_yorum) if yakin_yorum else None,
        dilimler=dilimler, ilgi_goren=ilgi,
    )
    if n < 20:
        r.uyarilar.append(f"Liste {n} üründen oluşuyor; 20 ve üzeri ürünle konum daha güvenilir olur.")
    if ilgi is None:
        r.uyarilar.append(f"İlgi gören fiyat aralığı için yorum sayısı bilinen en az {EN_AZ_YORUMLU} ürün gerekir.")
    return r


# ---------------------------------------------------------------- 3) rakip karşılaştırması


@dataclass
class Kiyas:
    olcu: str
    benim: str
    rakip_ortancasi: str
    sira: int | None  # 1 = en iyi
    kac_urun: int | None  # sıralamaya giren ürün sayısı (kullanıcının ürünü dahil)
    durum: str  # "önde", "geride", "aynı", "bilinmiyor"
    aciklama: str


@dataclass
class RakipRaporu:
    benim: Urun
    rakipler: list[Urun]  # fiyatı kullanıcının ürününe en yakın olanlar önce
    rakip_sayisi: int
    kiyaslar: list[Kiyas]
    onde: list[str]
    geride: list[str]
    uyarilar: list[str] = field(default_factory=list)


def _bicim(deger: float, tur: str) -> str:
    if tur == "tl":
        return tl(deger)
    if tur == "puan":
        return f"{deger:.1f}".replace(".", ",")
    return f"{deger:,.0f}".replace(",", ".")


def tl(tutar: float) -> str:
    return f"{tutar:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def _sayisal_kiyas(olcu: str, benim: float | None, rakip: list[float], dusuk_iyi: bool, tur: str) -> Kiyas | None:
    if not rakip:
        return None
    ortanca = median(rakip)
    if benim is None:
        return Kiyas(olcu, "bilinmiyor", _bicim(ortanca, tur), None, None, "bilinmiyor", "Ürününüz için bu bilgi verilmemiş.")
    daha_iyi = sum((r < benim) if dusuk_iyi else (r > benim) for r in rakip)
    sira, kac = daha_iyi + 1, len(rakip) + 1
    if benim == ortanca:
        durum = "aynı"
    else:
        durum = "önde" if (benim < ortanca) == dusuk_iyi else "geride"
    fark = benim - ortanca
    if tur == "tl":
        ne = f"rakip ortancasından {tl(abs(fark))} {'ucuz' if fark < 0 else 'pahalı'}" if fark else "rakip ortancasıyla aynı"
    else:
        ne = (f"rakip ortancasının {_bicim(abs(fark), tur)} {'altında' if fark < 0 else 'üstünde'}" if fark
              else "rakip ortancasıyla aynı")
    return Kiyas(olcu, _bicim(benim, tur), _bicim(ortanca, tur), sira, kac, durum, f"{kac} ürün içinde {sira}. sırada; {ne}.")


def rakip_karsilastir(benim: Urun | None, rakipler: list[Urun], gosterilecek: int = 10) -> RakipRaporu:
    if benim is None:
        raise ValueError("Rakip karşılaştırması için listede kendi ürününüz 'benim' sütununda işaretli olmalı")
    if not rakipler:
        raise ValueError("Rakip karşılaştırması için listede en az bir rakip ürün olmalı")
    kiyaslar = [k for k in (
        _sayisal_kiyas("Fiyat", benim.fiyat, [r.fiyat for r in rakipler], True, "tl"),
        _sayisal_kiyas("Puan", benim.puan, [r.puan for r in rakipler if r.puan is not None], False, "puan"),
        _sayisal_kiyas("Yorum sayısı", benim.yorum, [float(r.yorum) for r in rakipler if r.yorum is not None], False, "adet"),
        _sayisal_kiyas("Favori sayısı", benim.favori, [float(r.favori) for r in rakipler if r.favori is not None], False, "adet"),
    ) if k]
    kargolu = [r for r in rakipler if r.kargo_ucretsiz is not None]
    if kargolu:
        ucretsiz = sum(r.kargo_ucretsiz for r in kargolu)
        oran = f"{len(kargolu)} rakibin {ucretsiz} tanesinde ücretsiz"
        if benim.kargo_ucretsiz is None:
            kiyaslar.append(Kiyas("Kargo", "bilinmiyor", oran, None, None, "bilinmiyor", "Ürününüz için bu bilgi verilmemiş."))
        else:
            cogunluk = ucretsiz * 2 >= len(kargolu)
            if benim.kargo_ucretsiz and not cogunluk:
                durum = "önde"
            elif not benim.kargo_ucretsiz and cogunluk and ucretsiz:
                durum = "geride"
            else:
                durum = "aynı"
            kiyaslar.append(Kiyas("Kargo", "ücretsiz" if benim.kargo_ucretsiz else "ücretli", oran, None, None, durum,
                                  f"Kargo bilgisi olan {oran}."))
    r = RakipRaporu(
        benim=benim,
        rakipler=sorted(rakipler, key=lambda u: abs(u.fiyat - benim.fiyat))[:gosterilecek],
        rakip_sayisi=len(rakipler),
        kiyaslar=kiyaslar,
        onde=[k.olcu for k in kiyaslar if k.durum == "önde"],
        geride=[k.olcu for k in kiyaslar if k.durum == "geride"],
    )
    if len(rakipler) < 3:
        r.uyarilar.append(f"Yalnızca {len(rakipler)} rakip var; 3–5 rakiple karşılaştırma daha anlamlı olur.")
    if benim.yorum is not None and benim.yorum < 10:
        r.uyarilar.append("Ürününüzün yorum sayısı 10'dan az; puanı birkaç yorumla hızla değişebilir.")
    return r
