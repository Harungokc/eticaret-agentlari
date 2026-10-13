"""Yurt dışında çok satan ve yükselen ürünleri iki ayrı puanla değerlendirir.

- Satış gücü: ürün çok satıyor mu? (satış sırası, son dönem satış adedi, yorum sayısı)
- Yükseliş: ürün yeni mi parlıyor? (güncel kaynaklar, satışın ne kadarının son döneme ait olduğu, ilginin yönü)

Araç hiçbir siteye bağlanmaz. Ürün listesini asistan (internet aramasıyla, kaynak bağlantısı ve tarih
vererek) ya da kullanıcı hazırlar; buradaki her puan ve tutar o listedeki rakamlardan hesaplanır.
Bilinmeyen bir işaret tahmin edilmez: puana girmez, "kanıt" düzeyini düşürür.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from math import log10
from urllib.parse import quote, quote_plus, urlparse

# Satış gücü 100 üzerindendir; dört işaretin ağırlığı (puan, bilinen işaretler üzerinden hesaplanır):
AGIRLIK_SIRA, AGIRLIK_AYLIK, AGIRLIK_YORUM, AGIRLIK_TOPLAM = 40, 35, 25, 25
SIRA_UST = 10_000  # satış sırası 1 tam puan, 10.000 ve sonrası 0 puan; arası logaritmik
AYLIK_ALT, AYLIK_UST = 500, 100_000  # 30 günde satılan adet: altı 0 puan, üstü tam puan
YORUM_ALT, YORUM_UST = 100, 100_000
TOPLAM_ALT, TOPLAM_UST = 1_000, 1_000_000  # bugüne kadar satılan toplam adet

# Yükseliş 100 üzerindendir; üç işaretin ağırlığı:
AGIRLIK_YENILIK, AGIRLIK_IVME, AGIRLIK_YON, AGIRLIK_ARTIS, AGIRLIK_YENI_URUN = 35, 40, 25, 30, 20
YENI_GUN = 120  # kaynak bu kadar gün içinde yayımlandıysa "güncel" sayılır
YENILIK_PUANLARI = {0: 0, 1: 12, 2: 24}  # 3 ve üzeri güncel bağımsız kaynak tam puan alır
PAY_ALT, PAY_UST = 5.0, 40.0  # son 30 günün toplam satıştaki payı (yüzde): altı 0 puan, üstü tam puan
ORAN_ALT, ORAN_UST = 0.3, 10.0  # toplam satış bilinmiyorsa: 30 günlük satış ÷ yorum sayısı
ARTIS_ALT, ARTIS_UST = 10.0, 60.0  # satışın bir önceki aya göre artışı (yüzde): altı 0 puan, üstü tam puan; arası doğrusal
IVME_TABAN = 10_000  # toplam satışı bundan az olan üründe pay ölçülmez: birkaç yüz adetlik ürün her zaman "yeni" görünür
ORAN_TABAN_SATIS, ORAN_TABAN_YORUM = 2_000, 100  # satış ÷ yorum oranı için en az 30 günlük satış ve yorum sayısı
ARTIS_TABAN = 2_000  # aylık satışı bundan az üründe artış yüzdesi ölçülmez: 200 adetten 400'e çıkmak %100 görünür
YON_PUANLARI = {"yükseliyor": 25, "düz": 8, "düşüyor": 0}

ESIK_SATIS, ESIK_YUKSELIS = 50, 60  # bu puan ve üstü "çok satan" / "yükselen" sayılır
AZ_SATICI, ORTA_SATICI = 5, 20  # Türkiye'de aynı ürünü satan ilan sayısı eşikleri
ONCELIK_MARJ = 20.0  # yüzde

SINIFLAR = ("Çok satan ve yükselen", "Yeni yükselen", "Yükseliş adayı", "Çok satan", "Öne çıkmadı", "Kanıt yetersiz")
YUKSELENLER = SINIFLAR[:2]
COK_SATANLAR = (SINIFLAR[0], SINIFLAR[3])


@dataclass
class Aday:
    ad: str
    kategori: str = ""
    marka: str = ""
    orijinal_ad: str = ""  # ürünün kaynak sayfada yazan adı (yabancı dilde, markasıyla); arama bağlantıları bundan kurulur
    urun_linkleri: list[str] = field(default_factory=list)  # ürünün kendi sayfası (satış sayfası), görüldüyse
    gorsel: str = ""  # ürün fotoğrafının adresi, kaynak sayfada görüldüyse
    cince_ad: str = ""  # ürünün Çince arama terimi (ör. 钛砧板); Çin sitelerindeki arama bağlantıları bundan kurulur
    tedarik_fiyat: str = ""  # Çin'de görülen toptan ya da fabrika fiyatı, para birimiyle (ör. "¥18,5", "$2.40")
    tedarik_linkleri: list[str] = field(default_factory=list)  # o fiyatın görüldüğü tedarikçi sayfası
    tedarik_moq: str = ""  # en az sipariş adedi (ör. "500", "20-500")
    tedarikci: str = ""  # tedarikçinin adı ve bölgesi, görüldüyse
    yurtdisi_fiyat: str = ""  # kaynakta görülen fiyat, para birimiyle (ör. "$32.99")
    ulke: str = ""  # rakamların ait olduğu ülke ya da pazar (ör. ABD)
    kaynaklar: list[str] = field(default_factory=list)  # ürünün görüldüğü sayfaların bağlantıları
    kaynak_tarihleri: list[date | None] = field(default_factory=list)  # yazıların yayın tarihi, kaynaklarla aynı sırada; yoksa None
    satis_sirasi: int | None = None  # kendi kategorisindeki çok satanlar sırası
    yorum: int | None = None  # satış sayfasındaki yorum sayısı
    son_satis: int | None = None  # son dönemde satılan adet
    son_satis_gun: int | None = None  # o dönem kaç gün (ör. 7 ya da 30)
    toplam_satis: int | None = None  # bugüne kadar satılan toplam adet
    satis_degisim: float | None = None  # satışın bir önceki aya göre değişimi, yüzde (33.3 = %33,3 artış)
    veri_tarihi: date | None = None  # satış rakamlarının ait olduğu tarih
    izlenme: int | None = None  # video izlenmesi; puana girmez, bilgi olarak gösterilir
    trend: str | None = None  # arama ilgisinin yönü: yükseliyor / düz / düşüyor
    tr_satici: int | None = None  # Türkiye'de aynı ürünü satan ilan sayısı; 0 = arandı, bulunamadı
    tr_fiyat: float | None = None  # Türkiye'de görülen satış fiyatı (TL)
    tr_kontrol: str = ""  # "satıcı": satıcı kendi pazaryerinde baktı; "asistan": asistanın kaba sayımı
    tr_kaynaklar: list[str] = field(default_factory=list)  # Türkiye'de bakılan sayfalar; puana girmez
    maliyet: float | None = None  # ürünün satıcının kapısına kadarki toplam maliyeti (TL)
    satis_fiyati: float | None = None  # satıcının planladığı satış fiyatı (TL)
    komisyon: float | None = None  # pazaryeri komisyonu, yüzde
    kargo: float | None = None  # müşteriye gönderim masrafı (TL)
    aciklama: str = ""


@dataclass
class Puan:
    puan: int | None  # hiçbir işaret bilinmiyorsa None
    parcalar: dict[str, tuple[int, int]]  # işaret adı → (aldığı puan, alabileceği en çok puan); yalnızca bilinenler
    kanit: str  # güçlü / orta / zayıf / yok
    aciklamalar: list[str]  # puanın dayandığı rakamlar, okunur cümlelerle
    eksikler: list[str]  # bilinmeyen işaretler


@dataclass
class Kar:
    fiyat: float
    fiyat_kaynagi: str  # "planlanan fiyat" ya da "Türkiye'de görülen fiyat"
    maliyet: float
    komisyon_orani: float | None
    komisyon_tutari: float
    kargo: float
    net: float
    marj: float  # yüzde, satış fiyatına göre
    eksikler: list[str]  # hesaba katılamayan kalemler


@dataclass
class Risk:
    duzey: str  # yasak / izin / dikkat
    konu: str
    mesaj: str


@dataclass
class Degerlendirme:
    aday: Aday
    kaynak_sayisi: int
    satis: Puan
    yukselis: Puan
    sinif: str  # SINIFLAR içinden
    sinif_gerekce: str
    rekabet: str
    rekabet_aciklama: str
    kar: Kar | None
    riskler: list[Risk]
    karar: str  # Öncelikli / İncelenebilir / Öne çıkmadı / Kanıt yetersiz / Elenir
    gerekce: str


class AyTarihi(date):
    """Günü bilinmeyen tarih (ör. "2026-09"): ayın ilk günü olarak tutulur, yalnızca ay ve yıl olarak gösterilir."""


def yuvarla(deger: float, basamak: int = 0) -> float:
    """Yarımları yukarı yuvarlar (447,5 → 448); Excel'in gösterimiyle aynı sonucu verir."""
    return float(Decimal(str(deger)).quantize(Decimal(1).scaleb(-basamak), rounding=ROUND_HALF_UP))


def tl(tutar: float) -> str:
    return f"{yuvarla(tutar, 2):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def adet_yaz(n: float) -> str:
    return f"{int(yuvarla(n)):,}".replace(",", ".")


def yuzde_yaz(deger: float) -> str:
    return ("-" if deger < 0 else "") + "%" + f"{yuvarla(abs(deger), 1):.1f}".replace(".", ",")


def katla(metin: str) -> str:
    """Türkçe harfleri sadeleştirip küçültür ki anahtar kelime araması yazım farkına takılmasın."""
    metin = metin.replace("İ", "i").replace("I", "ı").lower()
    return metin.translate(str.maketrans("çğıöşüâîû", "cgiosuaiu"))


def alan_adi(baglanti: str) -> str:
    """Bağlantının site adını döndürür: https://www.ornek.com/x → ornek.com"""
    b = baglanti.strip()
    ag = urlparse(b if "//" in b else "//" + b).netloc.lower()
    ag = ag.split("@")[-1].split(":")[0]
    return ag[4:] if ag.startswith("www.") else ag


def kaynak_sayisi(kaynaklar: list[str]) -> int:
    """Aynı sitenin iki sayfası tek kaynak sayılır."""
    return len({alan_adi(k) for k in kaynaklar if alan_adi(k)})


def _logaritmik(deger: float, alt: float, ust: float, tavan: int) -> int:
    if deger <= alt:
        return 0
    if deger >= ust:
        return tavan
    return int(yuvarla(tavan * (log10(deger) - log10(alt)) / (log10(ust) - log10(alt))))


def _puan(parcalar: dict[str, tuple[int, int]], aciklamalar: list[str], eksikler: list[str]) -> Puan:
    """Bilinen işaretlerin puanını 100'e ölçekler; bilinmeyen işaret puanı düşürmez, kanıtı düşürür."""
    if not parcalar:
        return Puan(None, {}, "yok", aciklamalar, eksikler)
    alinan, tavan = sum(p for p, _ in parcalar.values()), sum(t for _, t in parcalar.values())
    kanit = {1: "zayıf", 2: "orta"}.get(len(parcalar), "güçlü")
    return Puan(int(yuvarla(100 * alinan / tavan)), parcalar, kanit, aciklamalar, eksikler)


def aylik_satis(a: Aday) -> float | None:
    """Son dönem satışını 30 güne çevirir (7 günde 700 adet → 3.000). Dönem bilinmiyorsa None."""
    if a.son_satis is None or not a.son_satis_gun:
        return None
    aylik = a.son_satis * 30 / a.son_satis_gun
    # Bir aydan yeni üründe oranlama toplam satışı aşar; ürün henüz satmadığı adetle çok satan sayılmasın.
    return min(aylik, toplam_satis(a)) if toplam_satis(a) else aylik


def toplam_satis(a: Aday) -> int | None:
    """Toplam satış; son dönem satışına eşit ya da ondan küçükse bilinmiyor sayılır.

    Bazı listeler toplamı bilinmeyen üründe haftalık rakamı toplam diye de yazar; bunu "bütün satış bu hafta
    oldu" diye okumak yanlış olur.
    """
    if a.toplam_satis is None or (a.son_satis is not None and a.toplam_satis <= a.son_satis):
        return None
    return a.toplam_satis


def satis_gucu(a: Aday) -> Puan:
    parcalar, aciklamalar, eksikler = {}, [], []
    if a.satis_sirasi is not None and a.satis_sirasi >= 1:
        parcalar["Satış sırası"] = (AGIRLIK_SIRA - _logaritmik(a.satis_sirasi, 1, SIRA_UST, AGIRLIK_SIRA), AGIRLIK_SIRA)
        aciklamalar.append(f"Kategorisinde çok satanlar sırası: {adet_yaz(a.satis_sirasi)}.")
    else:
        eksikler.append("satış sırası")
    aylik = aylik_satis(a)
    if aylik is not None:
        parcalar["Aylık satış"] = (_logaritmik(aylik, AYLIK_ALT, AYLIK_UST, AGIRLIK_AYLIK), AGIRLIK_AYLIK)
        if a.son_satis_gun == 30:
            aciklamalar.append(f"Son 30 günde yaklaşık {adet_yaz(a.son_satis)} adet satmış.")
        elif toplam_satis(a) and a.son_satis * 30 / a.son_satis_gun > a.toplam_satis:
            aciklamalar.append(f"Son {a.son_satis_gun} günde {adet_yaz(a.son_satis)} adet satmış; bir aydan yeni bir ürün.")
        else:
            aciklamalar.append(f"Son {a.son_satis_gun} günde {adet_yaz(a.son_satis)} adet satmış "
                               f"(30 güne oranlanınca yaklaşık {adet_yaz(aylik)}).")
    else:
        eksikler.append("son dönem satış adedi" if a.son_satis is None else "satış adedinin kaç güne ait olduğu")
    if a.yorum is not None:
        parcalar["Yorum"] = (_logaritmik(a.yorum, YORUM_ALT, YORUM_UST, AGIRLIK_YORUM), AGIRLIK_YORUM)
        aciklamalar.append(f"Satış sayfasında {adet_yaz(a.yorum)} yorum var.")
    else:
        eksikler.append("yorum sayısı")
    if toplam_satis(a) is not None:
        parcalar["Toplam satış"] = (_logaritmik(a.toplam_satis, TOPLAM_ALT, TOPLAM_UST, AGIRLIK_TOPLAM), AGIRLIK_TOPLAM)
        aciklamalar.append(f"Bugüne kadar {adet_yaz(a.toplam_satis)} adet satmış.")
    return _puan(parcalar, aciklamalar, eksikler)


def kaynak_ciftleri(a: Aday) -> list[tuple[str, date | None]]:
    """Her kaynağı yayın tarihiyle eşler; tarihi yazılmamış kaynağın tarihi None olur."""
    tarihler = list(a.kaynak_tarihleri) + [None] * len(a.kaynaklar)
    return list(zip(a.kaynaklar, tarihler))


def guncel_kaynak_sayisi(a: Aday, bugun: date) -> int | None:
    """Son YENI_GUN günde yayımlanmış, ürünü anlatan yazıların (haber, derleme, inceleme) kaç ayrı sitede olduğu.

    Yayın tarihi yalnızca yazılar için girilir; sürekli güncellenen satış listelerinin tarihi veri_tarihi'dir ve
    burada sayılmaz (liste güncel diye ürün yeni olmaz). Hiçbir kaynağın yayın tarihi yoksa None.
    """
    tarihli = [(alan_adi(k), t) for k, t in kaynak_ciftleri(a) if t is not None and alan_adi(k) and t <= bugun]
    if not tarihli:
        return None
    return len({alan for alan, t in tarihli if (bugun - t).days <= YENI_GUN})


def guvenli_adres(baglanti: str) -> str | None:
    """Bağlantıyı tıklanabilir adrese çevirir; http/https dışındakiler (javascript:, data: …) için None."""
    b = baglanti.strip()
    if "://" in b:
        return b if re.match(r"https?://", b, re.I) else None
    return None if ":" in b.split("/")[0] else "https://" + b


def inceleme_baglantilari(a: Aday) -> dict[str, list[tuple[str, str]]]:
    """Ürünü görmek için tıklanacak bağlantılar: {grup: [(etiket, adres)]}.

    Araç bu adreslere bağlanmaz; yalnızca arama adresini kurar. Yurt dışı aramaları ürünün kaynaktaki
    adıyla, Türkiye aramaları Türkçe adıyla yapılır.
    """
    tr = re.sub(r"\s*\([^)]*\)", "", a.ad).strip() or a.ad
    yd = a.orijinal_ad.strip()
    urun = [(f"Ürün sayfası ({alan_adi(k)})", adres) for k in a.urun_linkleri if (adres := guvenli_adres(k))]
    if yd:
        urun += [("Görseller", "https://www.google.com/search?tbm=isch&q=" + quote_plus(yd)),
                 ("Amazon'da ara", "https://www.amazon.com/s?k=" + quote_plus(yd))]
    else:
        urun.append(("Görseller", "https://www.google.com/search?tbm=isch&q=" + quote_plus(tr)))
    tedarik = [(f"Tedarikçi sayfası ({alan_adi(k)})", adres) for k in a.tedarik_linkleri if (adres := guvenli_adres(k))]
    cn = a.cince_ad.strip()
    if cn:
        # 1688 arama terimini GBK ile kodlanmış bekler; GBK'da olmayan harf varsa bağlantı kurulmaz.
        try:
            tedarik.append(("1688", "https://s.1688.com/selloffer/offer_search.htm?keywords=" + quote(cn.encode("gbk"))))
        except UnicodeEncodeError:
            pass
        tedarik.append(("Taobao", "https://s.taobao.com/search?q=" + quote_plus(cn)))
    if yd:
        kisa = " ".join(re.sub(r"[^A-Za-z0-9 ]", " ", yd).split()[:6])  # uzun ilan başlığı tedarik aramasını boğar
        tedarik += [("Alibaba", "https://www.alibaba.com/trade/search?SearchText=" + quote_plus(kisa or yd)),
                    ("AliExpress", "https://www.aliexpress.com/w/wholesale-" + quote((kisa or yd).replace(" ", "-")) + ".html"),
                    ("Made-in-China", "https://www.made-in-china.com/multi-search/" + quote_plus(kisa or yd).replace("+", "%2B") + "/F1/1.html"),
                    ("Temu", "https://www.temu.com/search_result.html?search_key=" + quote_plus(kisa or yd))]
    return {
        "Ürünü gör": urun,
        "Çin'de tedarik": tedarik,
        "Türkiye'de bak": [("Trendyol", "https://www.trendyol.com/sr?q=" + quote_plus(tr)),
                           ("Hepsiburada", "https://www.hepsiburada.com/ara?q=" + quote_plus(tr)),
                           ("Google Trends", "https://trends.google.com/trends/explore?geo=TR&date=today%2012-m&q=" + quote_plus(tr))],
    }


def guncel_ozet(a: Aday, bugun: date) -> tuple[int, date | None]:
    """Güncel yazıların kaç ayrı sitede olduğu ve en yenisinin tarihi."""
    guncel = [t for k, t in kaynak_ciftleri(a) if t is not None and alan_adi(k) and 0 <= (bugun - t).days <= YENI_GUN]
    return guncel_kaynak_sayisi(a, bugun) or 0, max(guncel, default=None)


def yukselis(a: Aday, bugun: date) -> Puan:
    parcalar, aciklamalar, eksikler = {}, [], []
    guncel = guncel_kaynak_sayisi(a, bugun)
    if guncel is not None:
        parcalar["Yenilik"] = (YENILIK_PUANLARI.get(guncel, AGIRLIK_YENILIK), AGIRLIK_YENILIK)
        aciklamalar.append(f"Son {YENI_GUN} günde yayımlanmış {guncel} ayrı sitedeki yazıda geçiyor." if guncel
                           else f"Hakkındaki yazıların hepsi {YENI_GUN} günden eski.")
    else:
        eksikler.append("ürünü anlatan güncel yazı")

    aylik = aylik_satis(a)
    eski_veri = a.veri_tarihi is not None and (bugun - a.veri_tarihi).days > YENI_GUN
    if aylik is not None and eski_veri:
        aciklamalar.append(f"Satış rakamı {YENI_GUN} günden eski; bugünkü yükselişi göstermediği için ölçülmedi.")
        eksikler.append("güncel satış rakamı")
    elif aylik is not None and toplam_satis(a) and a.toplam_satis >= IVME_TABAN:
        pay = min(100.0, 100 * aylik / a.toplam_satis)
        parcalar["İvme"] = (_logaritmik(pay, PAY_ALT, PAY_UST, AGIRLIK_IVME), AGIRLIK_IVME)
        aciklamalar.append(f"Bugüne kadarki {adet_yaz(a.toplam_satis)} adetlik satışının {yuzde_yaz(pay)} kadarı son 30 güne denk geliyor"
                           + (" (yeni ve hızlı)." if pay >= PAY_UST else " (yerleşik ürün)." if pay <= PAY_ALT else "."))
    elif aylik is not None and toplam_satis(a):
        aciklamalar.append(f"Toplam satışı henüz {adet_yaz(a.toplam_satis)} adet; {adet_yaz(IVME_TABAN)} adedin altında olduğu için "
                           "yükselişi ölçülmedi (küçük rakamlar yanıltır).")
        eksikler.append("satışın ne kadarının yeni olduğu (satış tabanı küçük)")
    elif aylik is not None and a.yorum and aylik >= ORAN_TABAN_SATIS and a.yorum >= ORAN_TABAN_YORUM:
        # Yorum sayısına göre çok satan ürün büyük olasılıkla yenidir; ama bu tek başına büyüdüğünü kanıtlamaz.
        oran = aylik / a.yorum
        parcalar["Yeni ürün"] = (_logaritmik(oran, ORAN_ALT, ORAN_UST, AGIRLIK_YENI_URUN), AGIRLIK_YENI_URUN)
        aciklamalar.append(f"30 günlük satışı yorum sayısının {_kat(oran)} katı"
                           + (" (yorum biriktirmeye vakit bulamamış; büyük olasılıkla yeni bir ürün)." if oran >= ORAN_UST
                              else " (uzun süredir satılan ürün)." if oran <= ORAN_ALT else ".")
                           + " Bu oran kaba bir göstergedir; tek başına yükseliş sayılmaz.")
        eksikler.append("satışın ne kadarının yeni olduğu")
    else:
        eksikler.append("satışın ne kadarının yeni olduğu")

    if a.satis_degisim is not None and not eski_veri and (aylik is None or aylik < ARTIS_TABAN):
        if a.satis_degisim > 0:
            aciklamalar.append(f"Satışı bir önceki aya göre {yuzde_yaz(a.satis_degisim)} artmış görünüyor, ama aylık satışı "
                               f"{adet_yaz(ARTIS_TABAN)} adedin altında olduğu için ölçülmedi (küçük rakamlarda yüzde yanıltır).")
    elif a.satis_degisim is not None and not eski_veri:
        oran = max(0.0, min(1.0, (a.satis_degisim - ARTIS_ALT) / (ARTIS_UST - ARTIS_ALT)))
        parcalar["Satış artışı"] = (int(yuvarla(AGIRLIK_ARTIS * oran)), AGIRLIK_ARTIS)
        aciklamalar.append(f"Satışı bir önceki aya göre {yuzde_yaz(abs(a.satis_degisim))} "
                           + ("arttı." if a.satis_degisim > 0 else "azaldı." if a.satis_degisim < 0 else "değişmedi."))

    if a.trend in YON_PUANLARI:
        parcalar["Yön"] = (YON_PUANLARI[a.trend], AGIRLIK_YON)
        aciklamalar.append(f"Arama ilgisi {a.trend}.")
    else:
        eksikler.append("arama ilgisinin yönü (Google Trends)")
    return _puan(parcalar, aciklamalar, eksikler)


def _kat(oran: float) -> str:
    return f"{yuvarla(oran, 1):.1f}".replace(".", ",")


def sinifla(kaynak_n: int, s: Puan, y: Puan) -> tuple[str, str]:
    """Ürünü iki puana göre sınıflar. Dönen değer: (sınıf, tek cümlelik gerekçe)."""
    if not kaynak_n:
        return "Kanıt yetersiz", "Kaynak bağlantısı yok; rakamların nereden geldiği doğrulanamıyor."
    if s.puan is None and y.puan is None:
        return "Kanıt yetersiz", "Ürün bir kaynakta geçiyor ama satış ya da yükselişe dair hiçbir rakam görülmedi."
    saglam = "İvme" in y.parcalar or "Satış artışı" in y.parcalar  # yükseliş yazıya değil, satış rakamına dayanıyor
    cok = s.puan is not None and s.puan >= ESIK_SATIS
    yuk = y.puan is not None and y.puan >= ESIK_YUKSELIS
    if yuk and saglam:
        if cok:
            return "Çok satan ve yükselen", f"Hem çok satıyor (satış gücü {s.puan}) hem hızlı büyüyor (yükseliş {y.puan})."
        return "Yeni yükselen", (f"Hızlı büyüyor (yükseliş {y.puan}); "
                                 + ("satış gücü henüz ölçülemedi." if s.puan is None else f"satış gücü henüz {s.puan}."))
    if cok:
        if y.puan is None:
            ek = "yükselip yükselmediği bilinmiyor."
        elif yuk:
            ek = "yeni bir ürün gibi görünüyor ama satışının arttığını gösteren rakam yok."
        else:
            ek = f"yeni bir yükseliş görünmüyor (yükseliş {y.puan}); yerleşik bir ürün."
        return "Çok satan", f"Çok satıyor (satış gücü {s.puan}); {ek}"
    yazi = y.parcalar.get("Yenilik", (0, 0))[0] > 0
    artiyor = y.parcalar.get("Yön", (0, 0))[0] == YON_PUANLARI["yükseliyor"]
    if (yazi or artiyor) and not saglam:
        dayanak = " ve ".join((["güncel yazılarda geçiyor"] if yazi else []) + (["arama ilgisi yükseliyor"] if artiyor else []))
        return "Yükseliş adayı", f"{dayanak.capitalize()}, ama yükselişi ölçecek satış rakamı görülemedi; doğrulanmadı."
    parcalar = ([f"satış gücü {s.puan}"] if s.puan is not None else []) + ([f"yükseliş {y.puan}"] if y.puan is not None else [])
    if yuk and not saglam:
        return "Öne çıkmadı", (f"Yeni bir ürün gibi görünüyor (yorumuna göre çok satıyor), ama satışının arttığını gösteren rakam yok"
                               f" ({', '.join(parcalar)}).")
    return "Öne çıkmadı", f"Görülen rakamlarla ne çok satan ne de yükselen sayıldı ({', '.join(parcalar)})."


def satici_bakti(a: Aday) -> bool:
    """Türkiye'deki sayıyı satıcı kendi pazaryerinde mi gördü? (Asistanın sayımı kaba ipucudur.)"""
    return a.tr_satici is not None and a.tr_kontrol == "satıcı"


def rekabet(a: Aday) -> tuple[str, str]:
    if a.tr_satici is None:
        return "bilinmiyor", "Türkiye'de satılıp satılmadığına bakılmadı."
    ek = "" if satici_bakti(a) else " Bu sayı asistanın tek bir sitede gördüğü kaba ipucudur; kendi pazaryerinizde doğrulayın."
    if a.tr_satici == 0:
        return "bulunamadı", ("Türkiye'de satan bulunamadı. Boşluk olabilir; ama talebin olmadığını ya da "
                              "ürünün getirilemediğini de gösterebilir." + ek)
    if a.tr_satici <= AZ_SATICI:
        return "az satıcı", f"Türkiye'de aynı ürün için {a.tr_satici} ilan sayıldı; pazar kalabalık değil." + ek
    if a.tr_satici <= ORTA_SATICI:
        return "orta", f"Türkiye'de aynı ürün için {a.tr_satici} ilan sayıldı; rekabet başlamış." + ek
    return "kalabalık", f"Türkiye'de aynı ürün için {a.tr_satici} ilan sayıldı; geç kalınmış olabilir, fiyat rekabeti beklenir." + ek


def kar_hesabi(a: Aday, varsayilan_komisyon: float | None = None, varsayilan_kargo: float | None = None) -> Kar | None:
    """Maliyet ve bir satış fiyatı biliniyorsa ürün başına kalan tutarı hesaplar; yoksa None."""
    fiyat, kaynak = a.satis_fiyati, "planlanan fiyat"
    if fiyat is None:
        fiyat, kaynak = a.tr_fiyat, "Türkiye'de görülen fiyat"
    if a.maliyet is None or fiyat is None or fiyat <= 0:
        return None
    oran = a.komisyon if a.komisyon is not None else varsayilan_komisyon
    kargo = a.kargo if a.kargo is not None else varsayilan_kargo
    eksikler = []
    if oran is None:
        eksikler.append("komisyon")
    if kargo is None:
        eksikler.append("kargo")
    komisyon_tutari = fiyat * (oran or 0) / 100
    net = fiyat - a.maliyet - komisyon_tutari - (kargo or 0)
    return Kar(fiyat, kaynak, a.maliyet, oran, komisyon_tutari, kargo or 0, net, net / fiyat * 100, eksikler)


# (düzey, konu, anahtar kelimeler, mesaj). Kelimeler katlanmış hâliyle, kelime başından aranır;
# sonu "!" ile biten kelime yalnızca tam kelime olarak eşleşir ("bicak!" → "bıçak", ama "bıçaklı" değil).
_RISK_KURALLARI = [
    ("yasak", "Elektronik sigara",
     ("elektronik sigara", "e-sigara", "e sigara", "vape", "puff bar", "isitilmis tutun"),
     "Elektronik sigara ve benzeri ürünlerin Türkiye'ye ithalatı yasaktır."),
    ("izin", "Kozmetik",
     ("kozmetik", "serum", "krem", "ruj", "maskara", "sampuan", "parfum", "cilt bakim", "sac boya", "makyaj seti", "makyaj urun", "makyaj malzeme",
      "dis beyazlat", "oje", "fondoten", "losyon", "peeling", "cilt maskesi", "yuz maskesi"),
     "Kozmetik ürün: satıştan önce Ürün Takip Sistemi (ÜTS) bildirimi ve Türkçe etiket gerekir."),
    ("izin", "Gıda ve takviye",
     ("gida", "takviye", "vitamin", "protein tozu", "atistirmalik", "sekerleme", "cikolata", "gummy",
      "mesrubat", "icecek tozu", "bitki cayi"),
     "Gıda ya da takviye edici gıda: Tarım ve Orman Bakanlığı izni ve Türkçe etiket gerekir."),
    ("izin", "Evcil hayvan maması ya da ödülü",
     ("mamasi", "mama!", "odulu!", "odul mama", "kopek biskuvi", "kedi biskuvi", "cigneme tablet", "cigneme kemig"),
     "Evcil hayvan maması ya da ödülü ise ithalatı Tarım ve Orman Bakanlığı iznine bağlıdır."),
    ("izin", "Veteriner ürünü",
     ("veteriner", "goz damla", "kulak damla", "pire", "kene", "ilac"),
     "Veteriner ilacı ya da hayvan sağlığı ürünü ise Tarım ve Orman Bakanlığı ruhsatı gerekir."),
    ("izin", "Dezenfektan ya da kimyasal ürün",
     ("dezenfektan", "koku giderici", "bocek kovucu", "sinek kovucu", "hasere"),
     "Dezenfektan, koku giderici ve benzeri biyosidal ürünlerde Sağlık Bakanlığı ruhsatı ya da bildirimi gerekir."),
    ("izin", "Tıbbi cihaz",
     ("tibbi", "medikal", "tansiyon", "nebulizator", "isitme cihazi", "kontakt lens", "seker olcer"),
     "Tıbbi cihaz sayılabilir: Ürün Takip Sistemi (ÜTS) kaydı gerekir."),
    ("dikkat", "Oyuncak ve bebek ürünü",
     ("oyuncak", "oyuncag", "bebek", "cocuk", "emzik", "biberon", "pelus"),
     "Çocuk oyuncağı ya da bebek ürünü ise CE işareti ve güvenlik belgeleri istenir."),
    ("dikkat", "Elektrikli ya da pilli ürün",
     ("sarjli", "sarj", "pilli", "batarya", "powerbank", "elektrikli", "usb", "led", "lamba", "blender", "kablosuz",
      "bluetooth", "isitici", "projektor", "projeksiyon", "adaptor", "kulaklik", "vantilator", "dijital", "buz makine", "kahve makine",
      "waffle makine", "dondurma makine", "tiras makine", "tuy kesme", "vakum makine", "ekmek makine", "sut makine", "dikis makine",
      "motorlu", "robot", "fritoz", "kettle", "tost makine", "kizartma makine", "kopurtucu", "termometre"),
     "Elektrikli ya da pilli üründe CE işareti gerekir; lityum pilli ürünlerin hava kargosu kısıtlıdır."),
    ("dikkat", "Kimyasal içerikli ürün",
     ("nem alici", "temizleyici", "deterjan", "leke cikar", "yapistirici", "kirec coz"),
     "Kimyasal içerikli üründe güvenlik bilgi formu ve Türkçe etiket istenebilir."),
    ("dikkat", "Bıçak ya da lazer",
     ("bicak!", "bicagi!", "bicaklar", "caki!", "lazer", "sustali"),
     "Bıçak ve lazer ürünlerinde pazaryerlerinin satış kısıtı olabilir."),
    ("dikkat", "Gıdayla temas eden ürün",
     ("mutfak", "tabak", "tabag", "bardak", "bardag", "kupa", "matara", "termos", "saklama kab", "kesme tahtasi", "tencere",
      "tava", "su sisesi", "yagdanlik", "yagdanlig", "baharat", "catal", "kasik", "kasig", "dograyici", "rende", "spatula"),
     "Gıdayla temas eden üründe gıdaya uygunluk belgesi istenebilir."),
]
_RISK_SIRASI = {"yasak": 0, "izin": 1, "dikkat": 2}
RISK_ETIKETI = {"yasak": "YASAK", "izin": "İZİN GEREKİR", "dikkat": "DİKKAT"}


def riskler(a: Aday) -> list[Risk]:
    metin = katla(f"{a.ad} {a.kategori}")
    bulunan = []
    for duzey, konu, kelimeler, mesaj in _RISK_KURALLARI:
        if any(re.search(rf"(?<![a-z0-9]){re.escape(k.rstrip('!'))}" + (r"(?![a-z0-9])" if k.endswith("!") else ""), metin)
               for k in kelimeler):
            bulunan.append(Risk(duzey, konu, mesaj))
    if a.marka.strip():
        bulunan.append(Risk("dikkat", "Markalı ürün",
                            "Markalı üründe marka sahibinin izni olmadan satış (taklit ürün, izinsiz ithalat) hukuki sorun çıkarabilir."))
    return sorted(bulunan, key=lambda r: _RISK_SIRASI[r.duzey])


def degerlendir(a: Aday, bugun: date, varsayilan_komisyon: float | None = None, varsayilan_kargo: float | None = None) -> Degerlendirme:
    n = kaynak_sayisi(a.kaynaklar)
    s, y = satis_gucu(a), yukselis(a, bugun)
    sinif, sinif_gerekce = sinifla(n, s, y)
    rek, rek_aciklama = rekabet(a)
    k = kar_hesabi(a, varsayilan_komisyon, varsayilan_kargo)
    r = riskler(a)

    yasak = next((x for x in r if x.duzey == "yasak"), None)
    izin = next((x for x in r if x.duzey == "izin"), None)
    if yasak:
        karar, gerekce = "Elenir", yasak.mesaj
    elif k and k.net <= 0:
        karar, gerekce = "Elenir", f"Bu fiyatla ürün başına {tl(abs(k.net))} zarar ediyor."
    elif sinif in ("Kanıt yetersiz", "Öne çıkmadı"):
        karar, gerekce = sinif, sinif_gerekce
    else:
        nedenler = []
        if sinif == "Yükseliş adayı":
            nedenler.append("yükselişi satış rakamıyla doğrulanmadı")
        if rek in ("orta", "kalabalık"):
            nedenler.append("Türkiye'de rekabet " + ("başlamış" if rek == "orta" else "kalabalık"))
        elif rek == "bilinmiyor":
            nedenler.append("Türkiye'deki rekabete bakılmadı")
        elif not satici_bakti(a):
            nedenler.append("Türkiye'deki ilan sayısını kendi pazaryerinizde doğrulamadınız")
        if k is None:
            nedenler.append("kâr hesaplanamadı (maliyet ya da satış fiyatı yok)")
        elif k.eksikler:
            nedenler.append(" ve ".join(k.eksikler) + " girilmedi")
        elif k.marj < ONCELIK_MARJ:
            nedenler.append(f"kâr marjı %{ONCELIK_MARJ:.0f}'nin altında ({yuzde_yaz(k.marj)})")
        if izin:
            nedenler.append(f"satış için izin ya da bildirim gerekiyor ({izin.konu.lower()})")
        if nedenler:
            karar, gerekce = "İncelenebilir", "Öncelikli sayılmadı: " + "; ".join(nedenler) + "."
        else:
            karar = "Öncelikli"
            gerekce = (f"{sinif}; Türkiye'de " + ("satan bulunamadı" if rek == "bulunamadı" else "az satıcı var")
                       + f"; kâr marjı {yuzde_yaz(k.marj)}.")
    return Degerlendirme(a, n, s, y, sinif, sinif_gerekce, rek, rek_aciklama, k, r, karar, gerekce)


def _sira(d: Degerlendirme) -> tuple:
    birincil = d.satis.puan if d.sinif == "Çok satan" else d.yukselis.puan
    ikincil = d.yukselis.puan if d.sinif == "Çok satan" else d.satis.puan
    if d.sinif in YUKSELENLER:  # aynı yükseliş puanında çok satan önce gelir
        ikincil = aylik_satis(d.aday)
    return (0 if d.sinif in YUKSELENLER else SINIFLAR.index(d.sinif), -(birincil if birincil is not None else -1), -(ikincil if ikincil is not None else -1), d.aday.ad)


def sirala(adaylar: list[Aday], bugun: date, varsayilan_komisyon: float | None = None,
           varsayilan_kargo: float | None = None) -> list[Degerlendirme]:
    """Önce gruba (yükselenler, izleme listesi, çok satanlar, diğerleri), sonra puana göre sıralar."""
    return sorted((degerlendir(a, bugun, varsayilan_komisyon, varsayilan_kargo) for a in adaylar), key=_sira)


def yukselenler(sonuc: list[Degerlendirme]) -> list[Degerlendirme]:
    return [d for d in sonuc if d.sinif in YUKSELENLER]


def adaylar(sonuc: list[Degerlendirme]) -> list[Degerlendirme]:
    """Yazılarda ya da arama ilgisinde öne çıkan ama satış rakamı görülemeyen ürünler: izleme listesi."""
    return [d for d in sonuc if d.sinif == "Yükseliş adayı"]


def cok_satanlar(sonuc: list[Degerlendirme]) -> list[Degerlendirme]:
    """Satış gücüne göre sıralı; "çok satan ve yükselen" ürünler iki listede de yer alır."""
    return sorted((d for d in sonuc if d.sinif in COK_SATANLAR), key=lambda d: (-(d.satis.puan or 0), d.aday.ad))


def bilgi_girilenler(sonuc: list[Degerlendirme]) -> list[Degerlendirme]:
    """Türkiye ya da maliyet bilgisi girilmiş ürünler; karar tablosunda yalnızca bunlar gösterilir."""
    return [d for d in sonuc if d.kar is not None or d.aday.tr_satici is not None or d.aday.maliyet is not None]


def derinlesti(sonuc: list[Degerlendirme]) -> bool:
    """Listede Türkiye ya da maliyet bilgisi var mı? Yoksa karar sütunu anlam taşımaz, gösterilmez."""
    return any(d.kar is not None or d.aday.tr_satici is not None for d in sonuc)


def digerleri(sonuc: list[Degerlendirme]) -> list[Degerlendirme]:
    return [d for d in sonuc if d.sinif in ("Öne çıkmadı", "Kanıt yetersiz")]


def iki_listede(sonuc: list[Degerlendirme]) -> int:
    return sum(1 for d in sonuc if d.sinif == "Çok satan ve yükselen")


@dataclass
class TedarikGrubu:
    """Aynı ürün türü için Çin'de görülen tedarik bilgisi ve o türdeki ürünler."""

    tur: str
    cince_ad: str
    fiyat: str
    moq: str
    tedarikci: str
    baglantilar: list[tuple[str, str]]
    urunler: list[Degerlendirme]
    yurtdisi: str  # o türdeki ürünlerin yurt dışı fiyat aralığı (aynı para birimindeyse)


def _fiyat_araligi(fiyatlar: list[str]) -> str:
    """["$24.89", "$35.99", "£19.99"] -> "$24.89-35.99 · £19.99". Tek fiyat olarak okunamayan değerler atlanır."""
    kume: dict[str, list[tuple[float, str]]] = {}
    for f in fiyatlar:
        m = re.fullmatch(r"\s*([$£€])\s*(\d+(?:[.,]\d{1,2})?)\s*", f)
        if m:
            kume.setdefault(m.group(1), []).append((float(m.group(2).replace(",", ".")), m.group(2)))
    parcalar = []
    for simge, degerler in sorted(kume.items(), key=lambda x: -len(x[1])):
        degerler.sort()
        parcalar.append(f"{simge}{degerler[0][1]}" if degerler[0][0] == degerler[-1][0] else f"{simge}{degerler[0][1]}-{degerler[-1][1]}")
    return " · ".join(parcalar)


def _ortak_ad(adlar: list[str]) -> str:
    """Ürün adlarının hepsinin sonunda geçen ortak kelimeler ("Cepli hamile taytı", "Hamile taytı" -> "Hamile taytı").

    Türkçede ürün türü adın sonundadır. En az iki kelimelik ortak son yoksa boş döner.
    """
    adlar = [x for x in adlar if x]
    if not adlar:
        return ""
    kelimeler = [[katla(k) for k in ad.split()] for ad in adlar]
    n = 0
    while all(len(k) > n for k in kelimeler) and len({k[-1 - n] for k in kelimeler}) == 1:
        n += 1
    if n < 2:
        return ""
    metin = " ".join(min(adlar, key=len).split()[-n:])
    return {"i": "İ", "ı": "I"}.get(metin[0], metin[0].upper()) + metin[1:]


def tedarik_gruplari(sonuc: list[Degerlendirme]) -> list[TedarikGrubu]:
    """Çin'de tedarik bilgisi girilmiş ürünleri türe göre toplar (kategori + Çince ad + fiyat aynıysa tek satır)."""
    gruplar: dict[tuple, TedarikGrubu] = {}
    for d in sonuc:
        a = d.aday
        if not (a.cince_ad.strip() or a.tedarik_fiyat.strip()):
            continue
        anahtar = (katla(a.kategori or a.ad), a.cince_ad.strip(), a.tedarik_fiyat.strip(), a.tedarik_moq.strip())
        if anahtar not in gruplar:
            tur = dict(inceleme_baglantilari(Aday(a.ad, cince_ad=a.cince_ad, tedarik_linkleri=a.tedarik_linkleri))["Çin'de tedarik"])
            gruplar[anahtar] = TedarikGrubu(a.kategori or a.ad, a.cince_ad.strip(), a.tedarik_fiyat.strip(), a.tedarik_moq.strip(),
                                            a.tedarikci.strip(), list(tur.items()), [], "")
        gruplar[anahtar].urunler.append(d)
    turdeki = {}
    for d in sonuc:
        turdeki[katla(d.aday.kategori or d.aday.ad)] = turdeki.get(katla(d.aday.kategori or d.aday.ad), 0) + 1
    for anahtar, g in gruplar.items():
        # Kategori çoğu zaman tedarik bilgisinden geniştir ("Doğum çantası" içinde yıkama şişesi). Grup kategorinin
        # tamamını kapsamıyorsa satır, o gruptaki en kısa ürün adıyla anılır.
        if len(g.urunler) < turdeki[anahtar[0]] or len(g.urunler) == 1:
            adlar = [re.sub(r"\s*\([^)]*\)", "", d.aday.ad).strip() for d in g.urunler]
            kisa = min((x for x in adlar if x), key=len, default=g.tur)
            g.tur = _ortak_ad(adlar) or (kisa + " ve benzerleri" if len(adlar) > 1 else kisa)
        g.yurtdisi = _fiyat_araligi([d.aday.yurtdisi_fiyat for d in g.urunler])
    return sorted(gruplar.values(), key=lambda g: (not g.fiyat, -len(g.urunler), katla(g.tur)))


TEDARIK_NOTU = ("Fabrika fiyatı, üretici dizinindeki benzer ürünlerin liste fiyatıdır (çoğunlukla FOB, dolar); nakliye, gümrük ve "
                "vergi dahil değildir, sipariş adedine ve pazarlığa göre değişir. Kâr hesabında kullanılmaz.")


def tedarik_sayilari(sonuc: list[Degerlendirme]) -> tuple[int, int]:
    """(fabrika fiyatı girilmiş ürün sayısı, Çince adı girilmiş ürün sayısı)."""
    return (sum(1 for d in sonuc if d.aday.tedarik_fiyat.strip()), sum(1 for d in sonuc if d.aday.cince_ad.strip()))
