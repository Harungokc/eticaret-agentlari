"""Sipariş listesinden satışların coğrafi dağılımını çıkarır: il, bölge, ilçe ve mahalle bazında;
sayılardan kurallarla bulgu ve öneri üretir.

Araç hiçbir siteye bağlanmaz ve adres çözümlemez; yalnızca sipariş listesindeki il, ilçe ve mahalle
sütunlarını sayar. Müşteri adı, telefon ve açık adres bu analiz için gerekmez ve okunmaz.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

EN_AZ_SIPARIS = 10
MAHALLE_EN_AZ = 3       # bundan az siparişi olan mahalle tek tek listelenmez (az sayı kişiyi işaret edebilir)
ORAN_EN_AZ = 20         # iade oranı ve ortalama sepet ancak bu kadar siparişi olan yerde yorumlanır
# Nüfusu en kalabalık 10 il (TÜİK adrese dayalı nüfus kayıt sistemi, 2023 sıralaması). Yalnızca "kalabalık
# olduğu hâlde sipariş gelmeyen il" bulgusunda kullanılır; araç nüfus sayısı içermez.
KALABALIK_ILLER = ("İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Konya", "Adana", "Şanlıurfa", "Gaziantep", "Kocaeli")

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
    mahalle: str = ""
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
class Oneri:
    tur: str      # Reklam, İlçe, Mahalle, Kargo, Sepet, İade, Boşluk, Ürün
    baslik: str
    bulgu: str    # listedeki sayılara dayanan gözlem
    oneri: str    # bu gözlemle ne yapılabileceği


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
    tum_ilceler: list[Satir] = field(default_factory=list)                 # ad: "İl / İlçe"; sınırsız
    il_ilceleri: dict[str, list[Satir]] = field(default_factory=dict)      # il → o ilin ilçeleri (ad: ilçe)
    ilce_mahalleleri: dict[str, list[Satir]] = field(default_factory=dict)  # "İl / İlçe" → mahalleleri (ad: mahalle)
    mahalleler: list[Satir] = field(default_factory=list)                  # ad: "İl / İlçe / Mahalle"
    mahalle_bilgisi_var: bool = False
    kucuk_mahalle: int = 0   # MAHALLE_EN_AZ altında kaldığı için listelenmeyen mahalle sayısı
    iade_orani: float | None = None  # genel, yüzde
    ortalama_sepet: float | None = None
    oneriler: list[Oneri] = field(default_factory=list)


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
    il_ilceleri, ilce_mahalleleri, mahalle_gruplari = {}, {}, defaultdict(list)
    for il, sips in il_gruplari.items():
        g = defaultdict(list)
        for s in sips:
            if s.ilce:
                g[baslik(s.ilce)].append(s)
        if g:
            il_ilceleri[il] = _satirlar(g, toplam, ciro, iade_var, urun_var)
    for anahtar, sips in ilce_gruplari.items():
        g = defaultdict(list)
        for s in sips:
            if s.mahalle:
                g[mahalle_adi(s.mahalle)].append(s)
        satirlar = _satirlar(g, toplam, ciro, iade_var, urun_var)
        for x in satirlar:
            mahalle_gruplari[f"{anahtar} / {x.ad}"] = g[x.ad]
        if satirlar:
            ilce_mahalleleri[anahtar] = satirlar
    tum_mahalleler = _satirlar(mahalle_gruplari, toplam, ciro, iade_var, urun_var)
    mahalle_var = sum(1 for s in taninan if s.mahalle) >= len(taninan) * 0.5
    r = Rapor(
        siparis_sayisi=toplam, ciro=ciro, il_sayisi=len(iller), iller=iller,
        bolgeler=_satirlar(bolge_gruplari, toplam, ciro, iade_var, urun_var),
        ilceler=_satirlar(ilce_gruplari, toplam, ciro, iade_var, urun_var)[:20],
        ilk3_pay=sum(s.pay for s in iller[:3]), ilk10_pay=sum(s.pay for s in iller[:10]),
        siparis_gelmeyen_iller=sorted((il for il in IL_BOLGESI if il not in il_gruplari), key=sade),
        taninmayan=len(taninmayan),
        taninmayan_ornekleri=[k for k, _ in Counter(s.il_ham.strip() or "(boş)" for s in taninmayan).most_common(5)],
        iptal=iptal, iade_bilgisi_var=iade_var, urun_bilgisi_var=urun_var,
        tum_ilceler=_satirlar(ilce_gruplari, toplam, ciro, iade_var, urun_var),
        il_ilceleri=il_ilceleri,
        ilce_mahalleleri={k: [x for x in v if x.siparis >= MAHALLE_EN_AZ] for k, v in ilce_mahalleleri.items()} if mahalle_var else {},
        mahalleler=[x for x in tum_mahalleler if x.siparis >= MAHALLE_EN_AZ] if mahalle_var else [],
        mahalle_bilgisi_var=mahalle_var,
        kucuk_mahalle=sum(1 for x in tum_mahalleler if x.siparis < MAHALLE_EN_AZ) if mahalle_var else 0,
        iade_orani=(100 * len({s.no or id(s) for s in taninan if s.iade}) / toplam) if iade_var else None,
        ortalama_sepet=(ciro / toplam) if ciro is not None else None,
    )
    if toplam < 100:
        r.uyarilar.append(f"Liste {toplam} siparişten oluşuyor; 100 ve üzeri siparişle il sıralaması daha güvenilir olur.")
    if r.taninmayan:
        r.uyarilar.append(f"{r.taninmayan} satırın ili tanınamadı ve analize girmedi (ör. {', '.join(r.taninmayan_ornekleri)}).")
    if ciro is None and tutarli:
        r.uyarilar.append("Siparişlerin bir kısmında tutar yok; ciro ve ortalama sepet hesaplanmadı.")
    if r.iade_bilgisi_var:
        r.uyarilar.append("İade oranı az siparişli illerde yanıltıcı olabilir; en az 20 siparişi olan illerde anlamlıdır.")
    if r.kucuk_mahalle:
        r.uyarilar.append(f"{MAHALLE_EN_AZ} siparişten azı olan {r.kucuk_mahalle} mahalle tek tek listelenmedi.")
    r.oneriler = oneriler(r)
    return r


def mahalle_adi(metin: str) -> str:
    """ "ATAKENT MAH.", "Atakent Mahallesi" → "Atakent" """
    ad = re.sub(r"\b(mahallesi|mahalle|mah|mh)\b\.?", "", metin.replace("İ", "i").replace("I", "ı").lower()).strip(" .,-")
    return baslik(ad or metin)


def _yz(x: float) -> str:
    return "%" + f"{x:.1f}".replace(".", ",")


def _tl(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".") + " TL"


def _say(adlar: list[str]) -> str:
    return adlar[0] if len(adlar) == 1 else ", ".join(adlar[:-1]) + " ve " + adlar[-1]


def oneriler(r: Rapor) -> list[Oneri]:
    """Sayılardan kurallarla bulgu ve öneri çıkarır. Her bulgu listedeki bir sayıya dayanır; eşikler README'de yazılıdır."""
    o: list[Oneri] = []
    ilk3 = [x.ad for x in r.iller[:3]]
    if r.ilk3_pay >= 50 and len(r.iller) >= 4:
        sonraki = [x.ad for x in r.iller[3:6]]
        o.append(Oneri("Reklam", f"Siparişlerde ilk üç ilin payı {_yz(r.ilk3_pay)}",
                       f"{r.siparis_sayisi} siparişte ilk üç il {_say(ilk3)}; birlikte payları {_yz(r.ilk3_pay)}, ilk 10 ilin payı {_yz(r.ilk10_pay)}.",
                       f"Reklam bütçesinin ana bölümünü bu üç ile ayırın; Türkiye geneli hedefleme bütçeyi sipariş gelmeyen "
                       f"illere dağıtır. Satışın bu kadar az ile bağlı olması aynı zamanda bir risktir: ikinci sıradaki illerde "
                       f"({', '.join(sonraki)}) küçük bütçeli denemeler yapın."))
    odak = []
    for il in r.iller[:3]:
        ilceler = r.il_ilceleri.get(il.ad, [])
        if il.siparis >= 30 and len(ilceler) >= 3:
            pay = 100 * sum(x.siparis for x in ilceler[:3]) / il.siparis
            if pay >= 40:
                odak.append((il, ilceler[:3], len(ilceler), pay))
    if odak:
        o.append(Oneri("İlçe", "Büyük illerde sipariş birkaç ilçede toplanıyor",
                       " ".join(f"{il.ad} ({il.siparis} sipariş): " + ", ".join(f"{x.ad} {x.siparis}" for x in ust)
                                + f"; {n} ilçe içinde ilk üçün payı {_yz(pay)}." for il, ust, n, pay in odak),
                       "Bu illerde il geneli yerine ilçe hedefli reklam deneyin; önce yukarıdaki ilçelerden başlayın. "
                       "Bu ilçelere hızlı teslimat yapabiliyorsanız ilanlarda belirtin."))
    ust_mahalle = [x for x in r.mahalleler if x.siparis >= 5][:5]
    if ust_mahalle:
        o.append(Oneri("Mahalle", "Siparişin yoğunlaştığı mahalleler belli",
                       "En çok sipariş gelen mahalleler: " + "; ".join(f"{x.ad.split(' / ')[2]} ({x.ad.split(' / ')[1]}, {x.siparis} sipariş)" for x in ust_mahalle) + ".",
                       "Konum hedefli reklamda (harita üzerinden yarıçap seçimi) bu mahalleleri merkez alın. Aynı mahalleden "
                       "tekrar eden sipariş, komşu tavsiyesinin işlediğini gösterebilir; paket içine indirim kodu koymayı deneyin."))
    if r.bolgeler and r.bolgeler[0].pay >= 35:
        b = r.bolgeler[0]
        o.append(Oneri("Kargo", f"{b.ad} bölgesinin sipariş payı {_yz(b.pay)}",
                       f"{b.siparis} sipariş {b.ad} bölgesine gitti" + (f"; ikinci sırada {r.bolgeler[1].ad} ({_yz(r.bolgeler[1].pay)})." if len(r.bolgeler) > 1 else "."),
                       f"Kargo firmasıyla görüşürken bu dağılımı gösterin ve {b.ad} bölgesi için ayrı fiyat isteyin. "
                       f"Depo ya da stok noktası seçecekseniz bu bölgeye yakınlık teslimat süresini kısaltır."))
    if r.ortalama_sepet:
        yuksek = [x for x in r.iller if x.siparis >= ORAN_EN_AZ and x.ortalama_sepet and x.ortalama_sepet >= r.ortalama_sepet * 1.08]
        dusuk = [x for x in r.iller if x.siparis >= ORAN_EN_AZ and x.ortalama_sepet and x.ortalama_sepet <= r.ortalama_sepet * 0.85]
        if yuksek:
            o.append(Oneri("Sepet", f"Sepet ortalamanın üstünde: {', '.join(x.ad for x in yuksek)}",
                           "; ".join(f"{x.ad}: ortalama sepet {_tl(x.ortalama_sepet)}" for x in yuksek) + f". Genel ortalama {_tl(r.ortalama_sepet)}.",
                           "Burada set, çoklu paket ve üst fiyatlı ürün reklamını deneyin; sipariş başına gelir daha yüksek "
                           "olduğu için reklam maliyetini daha kolay karşılar."))
        if dusuk:
            o.append(Oneri("Sepet", f"Sepet ortalamanın altında: {', '.join(x.ad for x in dusuk)}",
                           "; ".join(f"{x.ad}: ortalama sepet {_tl(x.ortalama_sepet)}" for x in dusuk) + f". Genel ortalama {_tl(r.ortalama_sepet)}.",
                           "Küçük sepette kargo maliyetinin payı büyür. Burada ikinci üründe indirim ya da belirli tutarın "
                           "üstüne ücretsiz kargo gibi sepeti büyüten bir kampanya deneyin."))
    if r.iade_orani is not None:
        esik = max(r.iade_orani * 1.5, r.iade_orani + 3)
        yerler = [x for x in r.iller + r.tum_ilceler if x.siparis >= ORAN_EN_AZ]
        sorunlu = [x for x in yerler if x.iade_orani is not None and x.iade_orani >= esik and x.iade >= 3]
        if sorunlu:
            o.append(Oneri("İade", f"İade oranı yüksek: {', '.join(x.ad for x in sorunlu)}",
                           "; ".join(f"{x.ad}: {x.siparis} siparişte {x.iade} iade ({_yz(x.iade_orani)})" for x in sorunlu)
                           + f". Genel iade oranı {_yz(r.iade_orani)}.",
                           "Buradaki iadelerin nedenine bakın: teslimat süresi, hasarlı kargo ya da ürün açıklamasıyla "
                           "uyuşmazlık. Neden kargoysa o bölge için başka bir kargo firması deneyin."))
        temiz = [x for x in r.iller if x.siparis >= 40 and x.iade == 0]
        if temiz and r.iade_orani > 0:
            o.append(Oneri("İade", f"İade görülmeyen il: {', '.join(x.ad for x in temiz)}",
                           "; ".join(f"{x.ad}: {x.siparis} siparişte iade yok" for x in temiz) + f". Genel iade oranı {_yz(r.iade_orani)}.",
                           "Burada reklamı artırmak iade maliyeti açısından daha güvenlidir. Neyin farklı olduğuna bakın "
                           "(kargo firması, teslimat süresi); aynısını iadenin yüksek olduğu yerlerde uygulamayı deneyin."))
    paylar = {x.ad: x.pay for x in r.iller}
    eksik = [il for il in KALABALIK_ILLER if paylar.get(il, 0) < 1]
    if eksik and r.siparis_sayisi >= 100:
        o.append(Oneri("Boşluk", f"Kalabalık illerden sipariş gelmiyor: {', '.join(eksik)}",
                       "Nüfusu en kalabalık 10 il içinde " + "; ".join(f"{il}: " + ("sipariş yok" if il not in paylar else f"sipariş payı {_yz(paylar[il])}") for il in eksik)
                       + f". Toplamda {len(r.siparis_gelmeyen_iller)} ilden hiç sipariş gelmedi.",
                       "Burada küçük bütçeli bir deneme reklamı açın. Sipariş yine gelmezse nedenine bakın: teslimat süresi "
                       "uzun mu, kargo ücreti yüksek mi, ürün o bölgeye uygun mu."))
    if r.urun_bilgisi_var and r.iller:
        genel = Counter()
        for x in r.iller:
            genel[x.en_cok_satan] += x.siparis
        ana = genel.most_common(1)[0][0]
        farkli = [x for x in r.iller if x.siparis >= 15 and x.en_cok_satan and x.en_cok_satan != ana][:3]
        if farkli:
            o.append(Oneri("Ürün", f"Öne çıkan ürünü farklı olan il: {', '.join(x.ad for x in farkli)}",
                           "; ".join(f"{x.ad}: en çok satan {x.en_cok_satan}" for x in farkli) + f". Çoğu ilde en çok satan {ana}.",
                           "Bu illere verdiğiniz reklamda orada öne çıkan ürünü gösterin; stok planını da buna göre yapın."))
    return o
