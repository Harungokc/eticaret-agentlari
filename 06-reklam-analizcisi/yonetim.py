"""Analiz sonucunu satıcının panelde yapacağı işlere çevirir ve bir sonraki raporda bu işlerin sonucunu izler.

Araç reklam hesabına bağlanmaz, hiçbir ayarı kendisi değiştirmez. Her iş satıcının panelde kendi eliyle yapacağı
bir adımdır: durdur, teklifi düşür, bütçeyi artır, negatif kelime ekle. Takip, iki dönemin raporunu karşılaştırır;
panel ayarlarını görmediği için "yapıldı mı" sorusunu yalnızca rapordaki rakamlardan çıkarır (ör. harcama sıfıra
indiyse reklam durdurulmuş sayılır).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from analiz import BUYUT_ORANI, EN_AZ_GOSTERIM, EN_AZ_SIPARIS, EN_AZ_TIKLAMA, Kalem, Rapor, anahtar

ARTIS = 20          # "bütçeyi artır" önerisinde dönem başına artış, yüzde (küçük adım)
EN_COK_DUSUS = 50   # teklif bundan fazla düşürülmesi gerekiyorsa reklam durdurulur
EN_AZ_DUSUS = 10

DURDUR, TEKLIF, ARTIR, NEGATIF, AYIR, FIYAT, GORSEL, SAYFA, DOKUNMA = (
    "Durdur", "Teklifi düşür", "Bütçeyi artır", "Negatif kelime ekle", "Ayrı kampanyaya al", "Fiyatı düzelt",
    "Görseli değiştir", "Ürün sayfasını düzelt", "Dokunma")


@dataclass
class Eylem:
    oncelik: int            # 1 hemen, 2 bu hafta, 3 izle
    is_: str                # DURDUR, TEKLIF, ...
    hedef: str              # ürün, kampanya ya da arama terimi
    tur: str                # "Ürün", "Kampanya", "Arama terimi"
    harcama: float          # dönemdeki harcama
    yeni_harcama: float | None   # aynı uzunlukta bir dönem için önerilen harcama
    degisim: int | None     # yüzde: -100 durdur, -30 teklif, +20 artır
    neden: str
    beklenen: str = ""


@dataclass
class Takip:
    is_: str
    hedef: str
    tur: str
    yapildi: str            # "Yapıldı", "Yapılmamış görünüyor", "Belirsiz"
    once: str               # önceki dönem özeti
    simdi: str              # bu dönem özeti
    sonuc: str              # "İyileşti", "Kötüleşti", "Değişmedi", ""
    yorum: str


@dataclass
class Yonetim:
    eylemler: list[Eylem] = field(default_factory=list)
    gun: int | None = None
    harcama: float = 0.0          # ürün/kampanya kalemlerinin dönem harcaması
    yeni_harcama: float = 0.0     # plan uygulanırsa
    kesilen: float = 0.0          # durdurulan ve düşürülenlerden serbest kalan
    eklenen: float = 0.0          # artırılanlara eklenen
    terim_kesilen: float = 0.0    # negatif kelimeyle kesilen arama terimi harcaması
    takip: list[Takip] = field(default_factory=list)
    onceki: Rapor | None = None
    harcama_simdi: float = 0.0    # takip için bu dönemin genel rakamları
    roas_simdi: float | None = None
    net_simdi: float | None = None


def _yz(x: float | None) -> str:
    return "—" if x is None else "%" + f"{x:.1f}".replace(".", ",")


def _tl(x: float | None) -> str:
    return "—" if x is None else f"{x:,.0f}".replace(",", ".") + " TL"


def _tl2(x: float | None) -> str:
    return "—" if x is None else f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def _kat(x: float | None) -> str:
    return "—" if x is None else f"{x:.2f}".replace(".", ",")


def _yukari_bes(x: float) -> int:
    return int(math.ceil(x / 5) * 5)


def _dusus(simdiki_oran: float, hedef_oran: float) -> int:
    """Reklam maliyet oranını hedefe indirmek için tıklama başı maliyetin yüzde kaç düşmesi gerektiği (5'e yuvarlanır)."""
    return max(EN_AZ_DUSUS, _yukari_bes(100 * (1 - hedef_oran / simdiki_oran)))


def _kalem_eylemi(k: Kalem, r: Rapor, tiklanmayan: set[str], satmayan: set[str]) -> Eylem:
    birim = r.birim
    yap = lambda o, i, yeni, d, neden, bek="": Eylem(o, i, k.ad, birim, k.harcama, yeni, d, neden, bek)  # noqa: E731

    if k.durum == "Reklamsız da zarar":
        return yap(1, DURDUR, 0.0, -100,
                   f"Ürün maliyeti, komisyon ve kargo satış fiyatını aşıyor (sipariş başına {_tl(k.birim_kar)}). "
                   "Her satış reklamsız da zarar ettiriyor.",
                   f"Dönemde {_tl(k.harcama)} reklam harcaması kesilir. Fiyatı düzeltmeden reklamı yeniden açmayın.")
    if k.durum == "Satış yok":
        return yap(1, DURDUR, 0.0, -100,
                   f"{k.tiklama or 0:.0f} tıklama aldı, hiç satış getirmedi.",
                   f"Dönemde {_tl(k.harcama)} boşa giden harcama kesilir. Önce ürün sayfasına bakın; sorun orada olabilir.")
    if k.durum == "Zarar":
        if k.acos and k.basa_bas_acos and k.basa_bas_acos > 0:
            gereken = _dusus(k.acos, k.basa_bas_acos)
            if k.basa_bas_acos < 5:
                return yap(1, DURDUR, 0.0, -100,
                           f"Ürün reklamdan önce sipariş başına yalnızca {_tl2(k.birim_kar)} kâr bırakıyor; tıklama başı "
                           f"{_tl2(k.tbm)} olan bir reklam bunu karşılayamaz.",
                           f"Dönemde reklam sonrası {_tl(-(k.net or 0))} zarar kesilir. Fiyatı ya da maliyeti düzeltmeden reklam vermeyin.")
            if gereken > EN_COK_DUSUS:
                return yap(1, DURDUR, 0.0, -100,
                           f"Reklam maliyet oranı {_yz(k.acos)}, başa baş {_yz(k.basa_bas_acos)}. Başa baş için tıklama "
                           "başı maliyetin yarıdan fazla düşmesi gerekir; bu kadar düşük teklifle reklam pek görünmez.",
                           f"Dönemde reklam sonrası {_tl(-(k.net or 0))} zarar kesilir.")
            return yap(1 if (k.net or 0) <= -100 else 2, TEKLIF, k.harcama * (1 - gereken / 100), -gereken,
                       f"Reklam maliyet oranı {_yz(k.acos)}, başa baş {_yz(k.basa_bas_acos)}; reklam sonrası {_tl(k.net)}.",
                       f"Teklif %{gereken} düşerse tıklama başı maliyet başa baş noktasına iner. Satış adedi de azalabilir; "
                       "iki hafta sonra yeni raporla bakın.")
        return yap(1, TEKLIF, k.harcama * 0.75, -25, f"Reklam sonrası {_tl(k.net)}.",
                   "Satış tutarı olmadığı için gereken düşüş hesaplanamadı; %25 ile başlayın.")
    if k.durum == "Kârlı" and k.acos is not None and k.basa_bas_acos:
        if k.acos <= k.basa_bas_acos * BUYUT_ORANI and (k.siparis or 0) >= 5:
            return yap(2, ARTIR, k.harcama * (1 + ARTIS / 100), ARTIS,
                       f"Reklam maliyet oranı {_yz(k.acos)}, başa baş {_yz(k.basa_bas_acos)}'in çok altında; "
                       f"reklam sonrası {_tl(k.net)}.",
                       f"Verim aynı kalırsa dönemde yaklaşık {_tl((k.net or 0) * ARTIS / 100)} ek kalan. Artıştan sonra oran "
                       "başa başa yaklaşırsa geri alın.")
    if not r.maliyet_var and r.acos is not None and k.acos is not None and (k.siparis or 0) >= EN_AZ_SIPARIS:
        if k.acos >= 2 * r.acos:
            gereken = min(EN_COK_DUSUS, _dusus(k.acos, r.acos))
            return yap(2, TEKLIF, k.harcama * (1 - gereken / 100), -gereken,
                       f"Reklam maliyet oranı {_yz(k.acos)}, genel oranın ({_yz(r.acos)}) iki katından fazla.",
                       "Maliyet bilgisi verilmediği için kâr hesaplanmadı; maliyeti verirseniz öneri kesinleşir.")
        if k.acos <= r.acos / 2 and (k.siparis or 0) >= 5:
            return yap(3, ARTIR, k.harcama * (1 + ARTIS / 100), ARTIS,
                       f"Reklam maliyet oranı {_yz(k.acos)}, genel oranın ({_yz(r.acos)}) yarısından az.",
                       "Maliyet bilgisi verilmediği için kâr ettirdiği kesin değil; önce maliyeti verin.")
    if k.ad in tiklanmayan:
        return yap(3, GORSEL, None, None, f"Tıklama oranı {_yz(k.ctr)}, genel oranın ({_yz(r.ctr)}) yarısından az.",
                   "Ana görseli ya da başlığı değiştirip iki hafta sonra tıklama oranını karşılaştırın.")
    if k.ad in satmayan:
        return yap(3, SAYFA, None, None, f"Dönüşüm {_yz(k.cvr)}, genel oranın ({_yz(r.cvr)}) yarısından az.",
                   "Fiyatı, yorumları, görselleri ve kargo süresini rakiplerle karşılaştırın.")
    if k.durum == "Az veri":
        return yap(3, DOKUNMA, k.harcama, 0, f"Karar için az veri: {k.siparis or 0:.0f} sipariş, {k.tiklama or 0:.0f} tıklama.",
                   "Bir dönem daha bekleyin.")
    if k.durum == "Kârlı" and k.acos is not None and k.basa_bas_acos and k.acos >= k.basa_bas_acos * 0.9:
        neden = (f"Başa başta: reklam maliyet oranı {_yz(k.acos)}, başa baş {_yz(k.basa_bas_acos)}; reklam sonrası "
                 f"{_tl(k.net)}. Bütçeyi artırmayın; oran yükselirse teklifi düşürün.")
    elif k.durum == "Kârlı":
        neden = f"Kârlı; reklam maliyet oranı {_yz(k.acos)}, başa baş {_yz(k.basa_bas_acos)}."
    elif not r.maliyet_var:
        neden = f"Reklam maliyet oranı {_yz(k.acos)}, genel orana yakın. Maliyet verilmediği için kâr ettirip ettirmediği bilinmiyor."
    else:
        neden = f"Reklam maliyet oranı {_yz(k.acos)}; maliyet bilgisi olmadığı için kâr hesaplanmadı."
    return yap(3, DOKUNMA, k.harcama, 0, neden, "")


def _terim_eylemi(t: Kalem, r: Rapor) -> Eylem | None:
    yap = lambda o, i, yeni, d, neden, bek="": Eylem(o, i, t.ad, "Arama terimi", t.harcama, yeni, d, neden, bek)  # noqa: E731
    if t.durum == "Satış yok":
        return yap(1, NEGATIF, 0.0, -100, f"{t.tiklama or 0:.0f} tıklama, hiç satış yok.",
                   f"Dönemde {_tl(t.harcama)} boşa giden harcama kesilir. Ürünle ilgili bir terimse önce teklifi düşürmeyi deneyin.")
    if r.acos is None or t.acos is None:
        return None
    if (t.tiklama or 0) >= EN_AZ_TIKLAMA and (t.siparis or 0) > 0 and t.acos >= 2 * r.acos:
        gereken = min(EN_COK_DUSUS, _dusus(t.acos, r.acos))
        return yap(2, TEKLIF, t.harcama * (1 - gereken / 100), -gereken,
                   f"Reklam maliyet oranı {_yz(t.acos)}, genel oranın ({_yz(r.acos)}) iki katından fazla.",
                   "Genel ve tek kelimelik terimler çok tıklanır, az satar. Daha dar bir terimle değiştirmeyi de deneyin.")
    if (t.siparis or 0) >= EN_AZ_SIPARIS and t.acos <= r.acos / 2:
        return yap(2, AYIR, t.harcama * (1 + ARTIS / 100), ARTIS,
                   f"Reklam maliyet oranı {_yz(t.acos)}, genel oranın yarısından az; {t.siparis:.0f} sipariş.",
                   "Tam eşlemeyle ayrı bir kampanyada hedefleyin ve teklifini koruyun; bütçesi başka terimlerle paylaşılmasın.")
    return None


def _butceye_ekle(y: Yonetim, harcama: float, yeni: float | None) -> None:
    yeni = harcama if yeni is None else yeni
    y.harcama += harcama
    y.yeni_harcama += yeni
    if yeni < harcama:
        y.kesilen += harcama - yeni
    else:
        y.eklenen += yeni - harcama


def planla(r: Rapor, gun: int | None = None) -> Yonetim:
    """Her ürün ya da kampanya için tek bir iş, her sorunlu arama terimi için bir iş çıkarır."""
    if gun is not None and gun <= 0:
        raise ValueError("--gun pozitif bir sayı olmalı, ör. 7")
    tiklanmayan = {k.ad for k in r.kalemler if r.ctr is not None and k.ctr is not None
                   and (k.gosterim or 0) >= EN_AZ_GOSTERIM and k.ctr <= r.ctr / 2}
    satmayan = {k.ad for k in r.kalemler if r.cvr is not None and k.cvr is not None and (k.tiklama or 0) >= EN_AZ_TIKLAMA
                and k.durum != "Satış yok" and k.cvr <= r.cvr / 2}
    y = Yonetim(gun=gun)
    # Arama terimi raporunda kampanya, terimlerin toplamıdır: bütçe terimlerden hesaplanır ve kampanyaya ayrıca
    # "dokunma" denmez (işler terimlerdedir).
    terim_raporu = bool(r.terimler) and r.birim == "Kampanya"
    for k in r.kalemler:
        if k.harcama < 1:
            continue  # bu dönemde harcaması olmayan (zaten durdurulmuş) reklam
        e = _kalem_eylemi(k, r, tiklanmayan, satmayan)
        if not (terim_raporu and e.is_ == DOKUNMA):
            y.eylemler.append(e)
        if not terim_raporu:
            _butceye_ekle(y, k.harcama, e.yeni_harcama)
    for t in r.terimler:
        if t.harcama < 1:
            continue
        e = _terim_eylemi(t, r)
        if e:
            y.eylemler.append(e)
            if e.is_ == NEGATIF:
                y.terim_kesilen += t.harcama
        if terim_raporu:
            _butceye_ekle(y, t.harcama, e.yeni_harcama if e else None)
    sira = {DURDUR: 0, NEGATIF: 1, TEKLIF: 2, FIYAT: 3, ARTIR: 4, AYIR: 5, GORSEL: 6, SAYFA: 7, DOKUNMA: 8}
    y.eylemler.sort(key=lambda e: (e.oncelik, sira[e.is_], -e.harcama, e.hedef))
    return y


def is_adi(e: Eylem) -> str:
    """"Teklifi düşür %45", "Bütçeyi artır %20", "Durdur" """
    if e.degisim in (None, 0, -100):
        return e.is_
    return f"{e.is_} %{abs(e.degisim)}"


def gunluk(y: Yonetim, tutar: float | None) -> str:
    """Panelde günlük bütçe girildiği için, dönem uzunluğu biliniyorsa günlük karşılığı."""
    if tutar is None or not y.gun:
        return ""
    return f"günde ~{_tl(tutar / y.gun)}"


# ------------------------------------------------------------------ takip: önceki dönemin işleri ne oldu

def _bul(kalemler: list[Kalem], ad: str) -> Kalem | None:
    a = anahtar(ad)
    return next((k for k in kalemler if anahtar(k.ad) == a), None)


def _ozet(k: Kalem | None, kar: bool) -> str:
    if k is None:
        return "raporda yok"
    parca = [f"harcama {_tl(k.harcama)}", f"ROAS {_kat(k.roas)}"]
    if kar and k.net is not None:
        parca.append(f"reklam sonrası {_tl(k.net)}")
    return ", ".join(parca)


def _sonuc(once: Kalem, simdi: Kalem, kar: bool) -> str:
    if kar and once.net is not None and simdi.net is not None:
        fark = simdi.net - once.net
        esik = max(50.0, abs(once.net) * 0.1)
        return "İyileşti" if fark > esik else "Kötüleşti" if fark < -esik else "Değişmedi"
    if once.acos is not None and simdi.acos is not None:
        fark = simdi.acos - once.acos
        return "İyileşti" if fark < -2 else "Kötüleşti" if fark > 2 else "Değişmedi"
    return ""


def izle(onceki: Rapor, simdi: Rapor, gun: int | None = None) -> list[Takip]:
    """Önceki raporun planını yeniden çıkarır ve her işin bu raporda yapılıp yapılmadığını, sonucunu yazar."""
    plan = planla(onceki, gun)
    kar = onceki.maliyet_var and simdi.maliyet_var
    sonuc: list[Takip] = []
    for e in plan.eylemler:
        if e.is_ == DOKUNMA:
            continue
        liste_once = onceki.terimler if e.tur == "Arama terimi" else onceki.kalemler
        liste_simdi = simdi.terimler if e.tur == "Arama terimi" else simdi.kalemler
        o, s = _bul(liste_once, e.hedef), _bul(liste_simdi, e.hedef)
        t = Takip(is_adi(e), e.hedef, e.tur, "Belirsiz", _ozet(o, kar), _ozet(s, kar), "", "")
        if e.is_ in (DURDUR, NEGATIF):
            if s is None or s.harcama < 1:
                t.yapildi = "Yapıldı"
                t.yorum = f"Harcama kesildi; dönemde {_tl(o.harcama if o else 0)} korundu."
                t.sonuc = "İyileşti" if e.oncelik == 1 else ""
            else:
                t.yapildi = "Yapılmamış görünüyor"
                t.yorum = f"Hâlâ {_tl(s.harcama)} harcama var" + (f" ve {s.siparis:.0f} sipariş." if s.siparis else ", satış yok.")
                t.sonuc = _sonuc(o, s, kar) if o else ""
        elif s is None or o is None:
            t.yapildi = "Belirsiz"
            t.yorum = "Bu dönemin raporunda yok; reklam durdurulmuş ya da adı değişmiş olabilir."
        elif e.is_ == TEKLIF:
            dustu = o.tbm is not None and s.tbm is not None and s.tbm <= o.tbm * 0.95
            t.yapildi = "Yapıldı" if dustu else "Yapılmamış görünüyor"
            t.sonuc = _sonuc(o, s, kar)
            t.yorum = (f"Tıklama başı maliyet {_tl2(o.tbm)} → {_tl2(s.tbm)}; reklam maliyet oranı {_yz(o.acos)} → {_yz(s.acos)}"
                       + (f" (başa baş {_yz(s.basa_bas_acos)})." if s.basa_bas_acos else "."))
            if dustu and s.durum == "Zarar":
                t.yorum += " Hâlâ zarar ettiriyor: teklifi biraz daha düşürün ya da durdurun."
        elif e.is_ in (ARTIR, AYIR):
            artti = s.harcama >= o.harcama * 1.1
            t.yapildi = "Yapıldı" if artti else "Yapılmamış görünüyor"
            t.sonuc = _sonuc(o, s, kar)
            t.yorum = f"Harcama {_tl(o.harcama)} → {_tl(s.harcama)}; reklam maliyet oranı {_yz(o.acos)} → {_yz(s.acos)}."
            if artti and t.sonuc == "Kötüleşti":
                t.yorum += " Artış verimi bozdu, sonuç geçen dönemden kötü: artışı geri alın."
            elif artti and s.basa_bas_acos and s.acos is not None and s.acos > s.basa_bas_acos * 0.85:
                t.yorum += " Oran başa başa yaklaştı: artışı geri alın."
            elif artti:
                t.yorum += f" Verim korunuyor; bir adım daha (%{ARTIS}) deneyebilirsiniz."
        else:  # görsel ya da sayfa: rapordan yalnızca oranın değişimi görülür
            once_oran, simdi_oran = (o.ctr, s.ctr) if e.is_ == GORSEL else (o.cvr, s.cvr)
            ad = "Tıklama oranı" if e.is_ == GORSEL else "Dönüşüm"
            t.yapildi = "Belirsiz"
            t.yorum = f"{ad} {_yz(once_oran)} → {_yz(simdi_oran)}. Değişikliği yaptıysanız etkisi bu."
            if once_oran is not None and simdi_oran is not None:
                t.sonuc = "İyileşti" if simdi_oran > once_oran * 1.1 else "Kötüleşti" if simdi_oran < once_oran * 0.9 else "Değişmedi"
        sonuc.append(t)
    return sonuc


def yonet(r: Rapor, onceki: Rapor | None = None, gun: int | None = None) -> Yonetim:
    y = planla(r, gun)
    if onceki is not None:
        y.onceki = onceki
        y.harcama_simdi, y.roas_simdi, y.net_simdi = r.harcama, r.roas, r.net
        y.takip = izle(onceki, r, gun)
    return y
