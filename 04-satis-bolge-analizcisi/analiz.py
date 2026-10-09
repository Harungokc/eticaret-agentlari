"""Sipariş listesinden satışların coğrafi dağılımını çıkarır: il, bölge ve ilçe bazında.

Araç hiçbir siteye bağlanmaz ve adres çözümlemez; yalnızca sipariş listesindeki il ve ilçe sütunlarını
sayar. Müşteri adı, telefon ve açık adres bu analiz için gerekmez ve okunmaz.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

EN_AZ_SIPARIS = 10

BOLGELER: dict[str, tuple[str, ...]] = {
    "Marmara": ("İstanbul", "Edirne", "Kırklareli", "Tekirdağ", "Çanakkale", "Kocaeli", "Yalova", "Sakarya", "Bilecik", "Bursa",
                "Balıkesir"),
    "Ege": ("İzmir", "Manisa", "Aydın", "Denizli", "Muğla", "Afyonkarahisar", "Kütahya", "Uşak"),
    "Akdeniz": ("Antalya", "Isparta", "Burdur", "Mersin", "Adana", "Hatay", "Osmaniye", "Kahramanmaraş"),
    "İç Anadolu": ("Ankara", "Konya", "Kayseri", "Eskişehir", "Sivas", "Kırıkkale", "Aksaray", "Karaman", "Kırşehir", "Niğde",
                   "Nevşehir", "Yozgat", "Çankırı"),
    "Karadeniz": ("Bolu", "Düzce", "Zonguldak", "Karabük", "Bartın", "Kastamonu", "Çorum", "Sinop", "Samsun", "Amasya", "Tokat",
                  "Ordu", "Giresun", "Gümüşhane", "Trabzon", "Bayburt", "Rize", "Artvin"),
    "Doğu Anadolu": ("Erzurum", "Erzincan", "Kars", "Ağrı", "Ardahan", "Iğdır", "Van", "Muş", "Bitlis", "Hakkari", "Bingöl",
                     "Tunceli", "Elazığ", "Malatya"),
    "Güneydoğu Anadolu": ("Gaziantep", "Şanlıurfa", "Diyarbakır", "Mardin", "Batman", "Siirt", "Şırnak", "Adıyaman", "Kilis"),
}
IL_BOLGESI = {il: bolge for bolge, iller in BOLGELER.items() for il in iller}
_HARF = str.maketrans("çğıöşüâîû", "cgiosuaiu")
_TAKMA = {"afyon": "Afyonkarahisar", "kmaras": "Kahramanmaraş", "maras": "Kahramanmaraş", "urfa": "Şanlıurfa", "sanliurfa": "Şanlıurfa",
          "antep": "Gaziantep", "icel": "Mersin", "izmit": "Kocaeli", "adapazari": "Sakarya", "antakya": "Hatay",
          "hakkari": "Hakkari", "hakkâri": "Hakkari"}


def sade(metin: str) -> str:
    """"İSTANBUL ", "istanbul", "Istanbul" → "istanbul" """
    kucuk = metin.replace("İ", "i").replace("I", "ı").lower().translate(_HARF)
    return re.sub(r"[^a-z]", "", kucuk)


_IL_ANAHTARI = {sade(il): il for il in IL_BOLGESI} | _TAKMA


def il_bul(metin: str | None) -> str | None:
    """Yazımı ne olursa olsun 81 ilden birine çevirir; tanınmazsa None."""
    if not metin:
        return None
    return _IL_ANAHTARI.get(sade(metin))


def baslik(metin: str) -> str:
    """İlçe adını düzgün yazıma çevirir: "KADIKÖY" → "Kadıköy" """
    kelimeler = []
    for k in " ".join(metin.split()).split(" "):
        k = k.replace("İ", "i").replace("I", "ı").lower()
        kelimeler.append(("İ" if k[:1] == "i" else k[:1].upper()) + k[1:])
    return " ".join(kelimeler)


@dataclass
class Siparis:
    il: str | None  # tanınan il adı; tanınmadıysa None
    il_ham: str = ""
    ilce: str = ""
    tutar: float | None = None
    urun: str = ""
    no: str = ""  # sipariş numarası; aynı siparişin birden çok satırı varsa bir kez sayılır
    iade: bool = False
    iptal: bool = False


@dataclass
class Satir:
    ad: str
    siparis: int
    pay: float  # yüzde
    ciro: float | None
    ciro_payi: float | None
    ortalama_sepet: float | None
    iade: int
    iade_orani: float | None  # yüzde; iade bilgisi yoksa None
    en_cok_satan: str = ""
    bolge: str = ""


@dataclass
class Rapor:
    siparis_sayisi: int
    ciro: float | None
    il_sayisi: int
    iller: list[Satir]
    bolgeler: list[Satir]
    ilceler: list[Satir]  # ad: "İl / İlçe"
    ilk3_pay: float
    ilk10_pay: float
    siparis_gelmeyen_iller: list[str]
    taninmayan: int  # ili tanınmayan satır
    taninmayan_ornekleri: list[str]
    iptal: int
    iade_bilgisi_var: bool
    urun_bilgisi_var: bool
    uyarilar: list[str] = field(default_factory=list)


def _satirlar(gruplar: dict[str, list[Siparis]], toplam: int, toplam_ciro: float | None, iade_var: bool,
              urun_var: bool, bolge_ver: bool = False) -> list[Satir]:
    sonuc = []
    for ad, sips in gruplar.items():
        adet = len({s.no for s in sips if s.no}) + sum(1 for s in sips if not s.no)
        tutarlar = [s.tutar for s in sips if s.tutar is not None]
        ciro = sum(tutarlar) if tutarlar and toplam_ciro is not None else None
        iade = len({s.no or id(s) for s in sips if s.iade})
        urunler = Counter(s.urun for s in sips if s.urun)
        sonuc.append(Satir(
            ad=ad, siparis=adet, pay=100 * adet / toplam, ciro=ciro,
            ciro_payi=(100 * ciro / toplam_ciro) if ciro is not None and toplam_ciro else None,
            ortalama_sepet=(ciro / adet) if ciro is not None and adet else None,
            iade=iade, iade_orani=(100 * iade / adet) if iade_var and adet else None,
            en_cok_satan=urunler.most_common(1)[0][0] if urun_var and urunler else "",
            bolge=IL_BOLGESI.get(ad, "") if bolge_ver else "",
        ))
    return sorted(sonuc, key=lambda s: (-s.siparis, s.ad))


def analiz_et(siparisler: list[Siparis]) -> Rapor:
    iptal = sum(1 for s in siparisler if s.iptal)
    gecerli = [s for s in siparisler if not s.iptal]
    taninan = [s for s in gecerli if s.il]
    taninmayan = [s for s in gecerli if not s.il]
    if len(taninan) < EN_AZ_SIPARIS:
        raise ValueError(f"Bu analiz için ili tanınan en az {EN_AZ_SIPARIS} sipariş gerekir; listede {len(taninan)} tane var")

    def adet(sips):
        return len({s.no for s in sips if s.no}) + sum(1 for s in sips if not s.no)

    toplam = adet(taninan)
    tutarli = [s.tutar for s in taninan if s.tutar is not None]
    ciro = sum(tutarli) if len(tutarli) >= len(taninan) * 0.9 else None  # tutarların çoğu yoksa ciro hesaplanmaz
    iade_var = any(s.iade for s in gecerli)
    urun_var = sum(1 for s in taninan if s.urun) >= len(taninan) * 0.5

    il_gruplari, bolge_gruplari, ilce_gruplari = defaultdict(list), defaultdict(list), defaultdict(list)
    for s in taninan:
        il_gruplari[s.il].append(s)
        bolge_gruplari[IL_BOLGESI[s.il]].append(s)
        if s.ilce:
            ilce_gruplari[f"{s.il} / {baslik(s.ilce)}"].append(s)
    iller = _satirlar(il_gruplari, toplam, ciro, iade_var, urun_var, bolge_ver=True)
    r = Rapor(
        siparis_sayisi=toplam, ciro=ciro, il_sayisi=len(iller), iller=iller,
        bolgeler=_satirlar(bolge_gruplari, toplam, ciro, iade_var, urun_var),
        ilceler=_satirlar(ilce_gruplari, toplam, ciro, iade_var, urun_var)[:20],
        ilk3_pay=sum(s.pay for s in iller[:3]), ilk10_pay=sum(s.pay for s in iller[:10]),
        siparis_gelmeyen_iller=sorted((il for il in IL_BOLGESI if il not in il_gruplari), key=sade),
        taninmayan=len(taninmayan),
        taninmayan_ornekleri=[k for k, _ in Counter(s.il_ham.strip() or "(boş)" for s in taninmayan).most_common(5)],
        iptal=iptal, iade_bilgisi_var=iade_var, urun_bilgisi_var=urun_var,
    )
    if toplam < 100:
        r.uyarilar.append(f"Liste {toplam} siparişten oluşuyor; 100 ve üzeri siparişle il sıralaması daha güvenilir olur.")
    if r.taninmayan:
        r.uyarilar.append(f"{r.taninmayan} satırın ili tanınamadı ve analize girmedi (ör. {', '.join(r.taninmayan_ornekleri)}).")
    if ciro is None and tutarli:
        r.uyarilar.append("Siparişlerin bir kısmında tutar yok; ciro ve ortalama sepet hesaplanmadı.")
    if r.iade_bilgisi_var:
        r.uyarilar.append("İade oranı az siparişli illerde yanıltıcı olabilir; en az 20 siparişi olan illerde anlamlıdır.")
    return r
