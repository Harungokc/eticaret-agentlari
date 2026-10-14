"""Reklam raporunu ürün (ya da kampanya) ve arama terimi bazında toplar; harcama, satış, reklam getirisi,
tıklama oranı ve dönüşümü hesaplar. Maliyet bilgisi verilirse reklam sonrası kârı ve başa baş noktasını
çıkarır. Sayılardan kurallarla bulgu ve öneri üretir.

Araç hiçbir siteye bağlanmaz; yalnızca satıcının panelden indirdiği reklam raporunu okur.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

EN_AZ_TIKLAMA = 20      # bir kalemin "satış getirmiyor" ya da "dönüşümü düşük" sayılması için gereken tıklama
EN_AZ_GOSTERIM = 1000   # tıklama oranı ancak bu kadar gösterimi olan kalemde yorumlanır
EN_AZ_SIPARIS = 3       # kârlılık ve reklam getirisi yorumu için gereken sipariş
BUYUT_ORANI = 0.6       # reklam maliyet oranı başa baş oranının bu katının altındaysa "büyütmeyi deneyin"


@dataclass
class ReklamSatiri:
    urun: str = ""
    kampanya: str = ""
    terim: str = ""
    harcama: float = 0.0
    ciro: float | None = None
    siparis: float | None = None
    tiklama: float | None = None
    gosterim: float | None = None


@dataclass
class Maliyet:
    """Ürün başına reklam öncesi giderler. Komisyon oran olarak (0,20 = %20) tutulur."""
    urun: str
    birim_maliyet: float = 0.0
    komisyon: float = 0.0
    kargo: float = 0.0
    fiyat: float | None = None


@dataclass
class Kalem:
    ad: str
    harcama: float
    ciro: float | None
    siparis: float | None
    tiklama: float | None
    gosterim: float | None
    kampanya: str = ""
    # türetilenler
    roas: float | None = None          # ciro / harcama
    acos: float | None = None          # harcama / ciro, yüzde
    ctr: float | None = None           # tıklama / gösterim, yüzde
    cvr: float | None = None           # sipariş / tıklama, yüzde
    tbm: float | None = None           # tıklama başı maliyet
    siparis_basi: float | None = None  # sipariş başı reklam maliyeti
    harcama_payi: float = 0.0          # yüzde
    ciro_payi: float | None = None     # yüzde
    # maliyet bilgisi varsa
    birim_kar: float | None = None     # reklam öncesi, sipariş başına
    basa_bas_acos: float | None = None  # yüzde: bu oranın üstünde reklam zarar ettirir
    net: float | None = None           # siparis × birim_kar − harcama
    durum: str = ""                    # "Zarar", "Kârlı", "Satış yok", "Az veri", ""


@dataclass
class Oneri:
    tur: str      # Bütçe, Zarar, Büyüt, Terim, Görsel, Sayfa, Veri
    baslik: str
    bulgu: str
    oneri: str


@dataclass
class Rapor:
    satir_sayisi: int
    harcama: float
    ciro: float | None
    siparis: float | None
    tiklama: float | None
    gosterim: float | None
    roas: float | None
    acos: float | None
    ctr: float | None
    cvr: float | None
    tbm: float | None
    birim: str                     # "Ürün" ya da "Kampanya"
    kalemler: list[Kalem]
    terimler: list[Kalem]
    oneriler: list[Oneri] = field(default_factory=list)
    uyarilar: list[str] = field(default_factory=list)
    maliyet_var: bool = False
    kar_marji: float | None = None  # --kar-marji ile verilen genel kâr payı, yüzde
    net: float | None = None
    eslesmeyen: list[str] = field(default_factory=list)  # maliyet dosyasında bulunmayan ürünler
    satis_getirmeyen_harcama: float = 0.0


_HARF = str.maketrans("çğıöşüâîû", "cgiosuaiu")


def anahtar(metin: str) -> str:
    """Ürün adlarını karşılaştırmak için: büyük-küçük harf, Türkçe harf ve boşluk farkı yok sayılır."""
    kucuk = str(metin).replace("İ", "i").replace("I", "ı").lower().translate(_HARF)
    return re.sub(r"[^a-z0-9]", "", kucuk)


def _bol(a: float | None, b: float | None, kat: float = 1.0) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return kat * a / b


def _topla(degerler: list[float | None]) -> float | None:
    dolu = [d for d in degerler if d is not None]
    return sum(dolu) if dolu else None


def _kalem(ad: str, satirlar: list[ReklamSatiri], toplam_harcama: float, toplam_ciro: float | None) -> Kalem:
    k = Kalem(ad=ad, harcama=sum(s.harcama for s in satirlar), ciro=_topla([s.ciro for s in satirlar]),
              siparis=_topla([s.siparis for s in satirlar]), tiklama=_topla([s.tiklama for s in satirlar]),
              gosterim=_topla([s.gosterim for s in satirlar]))
    kampanyalar = sorted({s.kampanya for s in satirlar if s.kampanya})
    k.kampanya = ", ".join(kampanyalar[:3]) + (f" (+{len(kampanyalar) - 3})" if len(kampanyalar) > 3 else "")
    k.roas = _bol(k.ciro, k.harcama)
    k.acos = _bol(k.harcama, k.ciro, 100) if k.ciro else None
    k.ctr = _bol(k.tiklama, k.gosterim, 100)
    k.cvr = _bol(k.siparis, k.tiklama, 100)
    k.tbm = _bol(k.harcama, k.tiklama)
    k.siparis_basi = _bol(k.harcama, k.siparis)
    k.harcama_payi = _bol(k.harcama, toplam_harcama, 100) or 0.0
    k.ciro_payi = _bol(k.ciro, toplam_ciro, 100) if toplam_ciro else None
    return k


def _grupla(satirlar: list[ReklamSatiri], alan: str, toplam_harcama: float, toplam_ciro: float | None) -> list[Kalem]:
    gruplar: dict[str, tuple[str, list[ReklamSatiri]]] = {}
    for s in satirlar:
        ad = " ".join(getattr(s, alan).split())
        if not ad:
            continue
        gruplar.setdefault(anahtar(ad) or ad, (ad, []))[1].append(s)
    kalemler = [_kalem(ad, liste, toplam_harcama, toplam_ciro) for ad, liste in gruplar.values()]
    return sorted(kalemler, key=lambda k: (-k.harcama, k.ad))


def _kar_ekle(k: Kalem, m: Maliyet | None, kar_marji: float | None) -> None:
    """Reklam öncesi sipariş başına kârı ve başa baş reklam maliyet oranını ekler."""
    fiyat = (m.fiyat if m and m.fiyat else None) or _bol(k.ciro, k.siparis)
    if m is not None and fiyat:
        k.birim_kar = fiyat - m.birim_maliyet - fiyat * m.komisyon - m.kargo
        k.basa_bas_acos = 100 * k.birim_kar / fiyat
    elif kar_marji is not None and fiyat:
        k.birim_kar = fiyat * kar_marji / 100
        k.basa_bas_acos = kar_marji
    if k.birim_kar is not None and k.siparis is not None:
        k.net = k.siparis * k.birim_kar - k.harcama


def _durum(k: Kalem, maliyet_var: bool) -> str:
    if (k.siparis == 0 or k.ciro == 0) and (k.tiklama or 0) >= EN_AZ_TIKLAMA:
        return "Satış yok"
    if not k.siparis or k.siparis < EN_AZ_SIPARIS:
        return "Az veri"
    if maliyet_var and k.net is not None:
        if k.birim_kar is not None and k.birim_kar <= 0:
            return "Reklamsız da zarar"
        return "Zarar" if k.net < 0 else "Kârlı"
    return ""


def _yz(x: float | None) -> str:
    return "" if x is None else "%" + f"{x:.1f}".replace(".", ",")


def _tl(x: float | None) -> str:
    return "" if x is None else f"{x:,.0f}".replace(",", ".") + " TL"


def _sayi(x: float | None) -> str:
    return "" if x is None else f"{x:,.0f}".replace(",", ".")


def _adlar(kalemler: list[Kalem], n: int = 3) -> str:
    adlar = [k.ad for k in kalemler[:n]]
    ek = f" ve {len(kalemler) - n} kalem daha" if len(kalemler) > n else ""
    return ", ".join(adlar) + ek


def oneriler(r: Rapor) -> list[Oneri]:
    """Sayılardan kurallarla bulgu ve öneri çıkarır. Eşikler bu dosyanın başında ve README'de yazılıdır."""
    o: list[Oneri] = []
    birim = r.birim.lower()

    bos = [k for k in r.kalemler if k.durum == "Satış yok"]
    if bos:
        tutar = sum(k.harcama for k in bos)
        o.append(Oneri("Bütçe", f"Satış getirmeyen reklam harcaması: {_tl(tutar)} ({_yz(_bol(tutar, r.harcama, 100))})",
                       f"En az {EN_AZ_TIKLAMA} tıklama aldığı hâlde hiç satış getirmeyen {len(bos)} {birim}: "
                       + "; ".join(f"{k.ad} ({_tl(k.harcama)}, {_sayi(k.tiklama)} tıklama)" for k in bos[:5])
                       + (f" ve {len(bos) - 5} {birim} daha." if len(bos) > 5 else "."),
                       "Bu reklamları durdurun ya da teklifi düşürün. Önce ürün sayfasına bakın: fiyat, görsel ve yorumlar "
                       "rakiplerin gerisindeyse tıklayan alıcı satın almıyor demektir; reklam bunu düzeltmez."))

    if len(r.kalemler) >= 4 and r.ciro:
        ust = r.kalemler[:3]
        h_pay = sum(k.harcama_payi for k in ust)
        c_pay = sum(k.ciro_payi or 0 for k in ust)
        if h_pay >= 50 and h_pay - c_pay >= 15:
            o.append(Oneri("Bütçe", f"Bütçenin {_yz(h_pay)}'i üç {birim}e gidiyor, satışın yalnızca {_yz(c_pay)}'i oradan geliyor",
                           f"En çok harcama yapılan üç {birim}: " + "; ".join(f"{k.ad} (harcama payı {_yz(k.harcama_payi)}, "
                                                                            f"satış payı {_yz(k.ciro_payi or 0)})" for k in ust) + ".",
                           f"Bütçeyi satış payı harcama payından yüksek olan {birim}lere kaydırmayı deneyin; aşağıdaki tabloda "
                           "reklam getirisi (ROAS) en yüksek olanlar ilk adaylardır."))

    if r.maliyet_var:
        zarar = sorted([k for k in r.kalemler if k.durum == "Zarar"], key=lambda k: k.net or 0)
        if zarar:
            o.append(Oneri("Zarar", f"Reklamı zarar ettiren {len(zarar)} {birim}: toplam {_tl(-sum(k.net or 0 for k in zarar))}",
                           "Reklam maliyet oranı başa baş oranını aşıyor: "
                           + "; ".join(f"{k.ad} (reklam maliyet oranı {_yz(k.acos)}, başa baş {_yz(k.basa_bas_acos)}, "
                                       f"reklam sonrası {_tl(k.net)})" for k in zarar[:5]) + ".",
                           "Panelde bu reklamların getirisi iyi görünse bile ürün maliyeti, komisyon ve kargo düşülünce para "
                           "kaybettiriyor. Teklifi düşürün ya da fiyatı gözden geçirin; satış adedi için bilerek zarar "
                           "ediyorsanız bunun bir sınırı olsun."))
        eksi = [k for k in r.kalemler if k.durum == "Reklamsız da zarar"]
        if eksi:
            o.append(Oneri("Zarar", f"{len(eksi)} {birim} reklamsız da zarar ediyor",
                           "Ürün maliyeti, komisyon ve kargo satış fiyatını aşıyor: "
                           + "; ".join(f"{k.ad} (sipariş başına {_tl(k.birim_kar)})" for k in eksi[:5]) + ".",
                           "Bu ürünlerde sorun reklam değil, fiyat ya da maliyet. Önce fiyatı ve maliyet bilgisini kontrol edin."))
        buyut = [k for k in r.kalemler if k.durum == "Kârlı" and k.acos is not None and k.basa_bas_acos
                 and k.acos <= k.basa_bas_acos * BUYUT_ORANI and (k.siparis or 0) >= 5]
        if buyut:
            o.append(Oneri("Büyüt", f"Reklamı rahat kâr ettiren {len(buyut)} {birim}",
                           "Reklam maliyet oranı başa baş oranının çok altında: "
                           + "; ".join(f"{k.ad} ({_yz(k.acos)}, başa baş {_yz(k.basa_bas_acos)}, reklam sonrası {_tl(k.net)})"
                                       for k in buyut[:5]) + ".",
                           "Bu reklamların bütçesini ya da teklifini küçük adımlarla (ör. haftada %20) artırmayı deneyin; "
                           "her adımdan sonra oranın başa baş çizgisinin altında kaldığına bakın."))
    elif r.acos is not None:
        pahali = [k for k in r.kalemler if k.acos is not None and (k.siparis or 0) >= EN_AZ_SIPARIS and k.acos >= 2 * r.acos]
        if pahali:
            o.append(Oneri("Zarar", f"Satışı en pahalıya gelen {len(pahali)} {birim}",
                           f"Genel reklam maliyet oranı {_yz(r.acos)}; bu {birim}lerde iki katından fazla: "
                           + "; ".join(f"{k.ad} ({_yz(k.acos)})" for k in pahali[:5]) + ".",
                           "Kâr edip etmediklerini görmek için maliyet dosyasını ya da kâr payınızı verin (--maliyet ya da "
                           "--kar-marji). O zamana kadar bu reklamların teklifini düşürmeyi düşünün."))

    tiklanmayan = []
    if r.ctr is not None:
        tiklanmayan = [k for k in r.kalemler if k.ctr is not None and (k.gosterim or 0) >= EN_AZ_GOSTERIM and k.ctr <= r.ctr / 2]
    if tiklanmayan:
        o.append(Oneri("Görsel", f"Görülüyor ama tıklanmıyor: {len(tiklanmayan)} {birim}",
                       f"Genel tıklama oranı {_yz(r.ctr)}; bu {birim}lerde yarısından az: "
                       + "; ".join(f"{k.ad} ({_sayi(k.gosterim)} gösterim, tıklama oranı {_yz(k.ctr)})" for k in tiklanmayan[:5]) + ".",
                       "Arama sonucunda alıcının gördüğü ilk şeye bakın: ana görsel, başlık, fiyat ve puan. Görseli ya da "
                       "başlığı değiştirip iki hafta sonra tıklama oranını yeniden karşılaştırın."))

    satmayan = []
    if r.cvr is not None:
        satmayan = [k for k in r.kalemler if k.cvr is not None and (k.tiklama or 0) >= EN_AZ_TIKLAMA
                    and k.durum != "Satış yok" and k.cvr <= r.cvr / 2]
    if satmayan:
        o.append(Oneri("Sayfa", f"Tıklanıyor ama az satıyor: {len(satmayan)} {birim}",
                       f"Genel dönüşüm oranı {_yz(r.cvr)}; bu {birim}lerde yarısından az: "
                       + "; ".join(f"{k.ad} ({_sayi(k.tiklama)} tıklama, dönüşüm {_yz(k.cvr)})" for k in satmayan[:5]) + ".",
                       "Alıcı ilgileniyor ama ürün sayfasında vazgeçiyor. Fiyatı rakiplerle, yorum ve puanı, beden ve ölçü "
                       "bilgisini, kargo süresini kontrol edin."))

    bos_terim = [t for t in r.terimler if t.durum == "Satış yok"]
    if bos_terim:
        tutar = sum(t.harcama for t in bos_terim)
        o.append(Oneri("Terim", f"Satış getirmeyen {len(bos_terim)} arama terimi: {_tl(tutar)}",
                       f"En az {EN_AZ_TIKLAMA} tıklama alıp hiç satış getirmeyen terimler: "
                       + "; ".join(f"\"{t.ad}\" ({_tl(t.harcama)})" for t in bos_terim[:8])
                       + (f" ve {len(bos_terim) - 8} terim daha." if len(bos_terim) > 8 else "."),
                       "Bu terimleri negatif anahtar kelime olarak ekleyin ya da teklifini düşürün. Ürününüzle ilgisiz "
                       "olanlar önce gelmeli."))
    pahali_terim = [t for t in r.terimler if t.durum != "Satış yok" and (t.tiklama or 0) >= EN_AZ_TIKLAMA and (t.siparis or 0) > 0
                    and t.acos is not None and r.acos is not None and t.acos >= 2 * r.acos]
    if pahali_terim:
        o.append(Oneri("Terim", f"Satışı çok pahalıya getiren {len(pahali_terim)} arama terimi",
                       f"Genel reklam maliyet oranı {_yz(r.acos)}; bu terimlerde iki katından fazla: "
                       + "; ".join(f"\"{t.ad}\" ({_yz(t.acos)}, {_sayi(t.tiklama)} tıklamada {_sayi(t.siparis)} sipariş)"
                                   for t in pahali_terim[:6]) + ".",
                       "Teklifi düşürün. Genel terimler (tek kelime) ve başka markaların adı çok tıklanır ama az satar; "
                       "bunları daha dar terimlerle değiştirmeyi deneyin."))
    iyi_terim = [t for t in r.terimler if (t.siparis or 0) >= EN_AZ_SIPARIS and t.acos is not None and r.acos is not None
                 and t.acos <= r.acos / 2][:5]
    if iyi_terim:
        o.append(Oneri("Terim", f"En verimli {len(iyi_terim)} arama terimi",
                       f"Genel reklam maliyet oranı {_yz(r.acos)}; bu terimlerde yarısından az: "
                       + "; ".join(f"\"{t.ad}\" ({_yz(t.acos)}, {_sayi(t.siparis)} sipariş)" for t in iyi_terim) + ".",
                       "Bu terimleri ayrı bir kampanyada tam eşleme ile hedefleyin; teklifini ve ürün başlığındaki yerini "
                       "güçlendirin."))
    return o


def analiz_et(satirlar: list[ReklamSatiri], maliyetler: list[Maliyet] | None = None, kar_marji: float | None = None) -> Rapor:
    if not satirlar:
        raise ValueError("Reklam raporunda okunabilen satır yok")
    if kar_marji is not None and not 0 < kar_marji < 100:
        raise ValueError("--kar-marji 0 ile 100 arasında bir yüzde olmalı, ör. 25")
    harcama = sum(s.harcama for s in satirlar)
    ciro = _topla([s.ciro for s in satirlar])
    birim = "Ürün" if any(s.urun for s in satirlar) else "Kampanya"
    alan = "urun" if birim == "Ürün" else "kampanya"
    kalemler = _grupla(satirlar, alan, harcama, ciro)
    terimler = _grupla(satirlar, "terim", harcama, ciro)
    if not kalemler and not terimler:
        raise ValueError("Raporda ürün, kampanya ya da arama terimi sütunu bulunamadı; satırlar gruplanamadı")

    tablo = {anahtar(m.urun): m for m in (maliyetler or [])}
    maliyet_var = bool(tablo) or kar_marji is not None
    eslesmeyen = []
    for k in kalemler:
        m = tablo.get(anahtar(k.ad))
        if tablo and m is None:
            eslesmeyen.append(k.ad)
        _kar_ekle(k, m, kar_marji if m is None else None)
        k.durum = _durum(k, maliyet_var)
    for t in terimler:
        t.durum = _durum(t, False)

    siparis = _topla([s.siparis for s in satirlar])
    tiklama = _topla([s.tiklama for s in satirlar])
    gosterim = _topla([s.gosterim for s in satirlar])
    r = Rapor(satir_sayisi=len(satirlar), harcama=harcama, ciro=ciro, siparis=siparis, tiklama=tiklama, gosterim=gosterim,
              roas=_bol(ciro, harcama), acos=_bol(harcama, ciro, 100) if ciro else None, ctr=_bol(tiklama, gosterim, 100),
              cvr=_bol(siparis, tiklama, 100), tbm=_bol(harcama, tiklama), birim=birim, kalemler=kalemler, terimler=terimler,
              maliyet_var=maliyet_var, kar_marji=kar_marji, eslesmeyen=eslesmeyen)
    netler = [k.net for k in kalemler if k.net is not None]
    r.net = sum(netler) if netler else None
    r.satis_getirmeyen_harcama = sum(k.harcama for k in kalemler if k.durum == "Satış yok")
    r.oneriler = oneriler(r)

    if ciro is None:
        r.uyarilar.append("Raporda satış tutarı sütunu bulunamadı; reklam getirisi (ROAS) ve kâr hesaplanamadı.")
    if siparis is None:
        r.uyarilar.append("Raporda sipariş ya da satış adedi sütunu bulunamadı; dönüşüm ve sipariş başı maliyet hesaplanamadı.")
    if eslesmeyen:
        r.uyarilar.append(f"Maliyet dosyasında bulunamayan {len(eslesmeyen)} ürünün kârı hesaplanmadı: "
                          + ", ".join(eslesmeyen[:6]) + (" …" if len(eslesmeyen) > 6 else "")
                          + ". Ürün adlarını reklam raporundaki gibi yazın.")
    if not maliyet_var and ciro:
        r.uyarilar.append("Maliyet bilgisi verilmediği için reklamın kâr ettirip ettirmediği hesaplanmadı. Ürün maliyeti, komisyon "
                          "ve kargoyu bir dosyayla (--maliyet) ya da genel kâr payınızı (--kar-marji) verin.")
    return r
