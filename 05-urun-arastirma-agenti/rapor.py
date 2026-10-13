"""Değerlendirme sonucunu Excel dosyasına çevirir."""

from __future__ import annotations

from datetime import date

from analiz import (AyTarihi, AZ_SATICI, ESIK_SATIS, ESIK_YUKSELIS, ONCELIK_MARJ, ORTA_SATICI, RISK_ETIKETI, YENI_GUN, Degerlendirme, Puan,
                    TEDARIK_NOTU, adaylar, aylik_satis, cok_satanlar, guncel_kaynak_sayisi, inceleme_baglantilari, kaynak_ciftleri, tedarik_gruplari,
                    yukselenler)
from xlsx import AFIS, DUZ, ETIKET, GIRDI_METIN, GIRDI_TL, GIRDI_YUZDE, NOT, ONDALIK, SARMA, SUTUN, TAM, TL, VURGU_TL, YUZDE, Formul, Sayfa, kitap_yaz

UYARI = ("Bu rapor yalnızca listedeki rakamlara dayanır ve bir satış garantisi değildir. Yurt dışında satması "
         "Türkiye'de satacağını göstermez. Kâr hesabı KDV, gelir vergisi, iade ve reklam giderini içermez. "
         "Risk uyarıları genel bilgidir, eksiksiz değildir; ithalat ve belge koşullarını gümrük müşavirinize sorun.")


def _t(t: date | None) -> str:
    return "" if not t else t.strftime("%m.%Y") if isinstance(t, AyTarihi) else t.strftime("%d.%m.%Y")


def _p(p: Puan):
    return "" if p.puan is None else p.puan


def _risk(d: Degerlendirme) -> str:
    return "\n".join(f"[{RISK_ETIKETI[r.duzey]}] {r.mesaj}" for r in d.riskler) or "Uyarı çıkmadı."


def _link(etiket: str, adres: str):
    """Tıklanabilir hücre. Excel'in bağlantı formülü 255 karakteri ve çift tırnağı kaldırmaz; öyleyse adres düz yazılır."""
    if len(adres) > 255 or '"' in adres:
        return adres
    return Formul(f'HYPERLINK("{adres}","{etiket}")', etiket)


def incele_sayfasi(sonuc: list[Degerlendirme]) -> Sayfa:
    s = Sayfa("Ürünleri incele", [36, 22, 44, 16, 14, 16, 12, 28, 14, 12, 12, 12, 10, 10, 12, 12, 14, 10, 12, 14, 16], dondur="B4")
    s.yaz("A1", "Ürünleri İnceleyin: Yurt Dışı, Çin'de Tedarik, Türkiye", AFIS)
    s.birlestir("A1:U1", 30)
    s.yaz("A2", "Hücrelere tıklayınca ilgili sayfa tarayıcıda açılır. Yurt dışı aramaları ürünün kaynaktaki adıyla, 1688 ve Taobao aramaları "
                "Çince adıyla, Türkiye aramaları Türkçe adıyla yapılır. Çin'de fabrika fiyatı liste fiyatıdır (nakliye, gümrük, vergi hariç). "
                "Arama sonuçlarında aynı ürünü bulmak için fotoğrafa bakın.", NOT)
    s.birlestir("A2:U2", 28)
    s.satir(3, ["Ürün", "Sınıf", "Listedeki adı", "Çince adı", "Yurt dışı fiyatı", "Çin'de fabrika fiyatı", "En az sipariş", "Tedarikçi",
                "Ürün sayfası", "Fotoğraf", "Görseller", "Amazon", "1688", "Taobao", "Alibaba", "AliExpress", "Made-in-China", "Temu", "Trendyol",
                "Hepsiburada", "Google Trends (TR)"], SUTUN)
    for i, d in enumerate(sonuc, 4):
        a, b = d.aday, inceleme_baglantilari(d.aday)
        gor = dict((e.split(" (")[0], adres) for e, adres in b["Ürünü gör"])
        cin = dict((e.split(" (")[0], adres) for e, adres in b["Çin'de tedarik"])
        tr = dict(b["Türkiye'de bak"])
        h = lambda sozluk, anahtar, etiket: _link(etiket, sozluk[anahtar]) if anahtar in sozluk else ""  # noqa: E731
        s.satir(i, [a.ad, d.sinif, a.orijinal_ad, a.cince_ad, a.yurtdisi_fiyat,
                    _link(a.tedarik_fiyat or "Tedarikçi", cin["Tedarikçi sayfası"]) if "Tedarikçi sayfası" in cin and '"' not in a.tedarik_fiyat
                    else a.tedarik_fiyat, a.tedarik_moq, a.tedarikci,
                    h(gor, "Ürün sayfası", "Ürünü aç"), _link("Fotoğraf", a.gorsel) if a.gorsel.lower().startswith("https://") else "",
                    h(gor, "Görseller", "Görseller"), h(gor, "Amazon'da ara", "Amazon"), h(cin, "1688", "1688"), h(cin, "Taobao", "Taobao"),
                    h(cin, "Alibaba", "Alibaba"), h(cin, "AliExpress", "AliExpress"), h(cin, "Made-in-China", "Made-in-China"), h(cin, "Temu", "Temu"),
                    h(tr, "Trendyol", "Trendyol"), h(tr, "Hepsiburada", "Hepsiburada"), h(tr, "Google Trends", "Trends")],
                [SARMA, DUZ, SARMA, DUZ, DUZ, DUZ, DUZ, SARMA] + [DUZ] * 13)
    return s


def tedarik_sayfasi(sonuc: list[Degerlendirme]) -> Sayfa:
    s = Sayfa("Çin'de tedarik", [34, 18, 16, 20, 14, 34, 16, 12, 12, 8, 60], dondur="B4")
    s.yaz("A1", "Çin'de Tedarik: Ürün Türü Başına Fabrika Fiyatı", AFIS)
    s.birlestir("A1:K1", 30)
    s.yaz("A2", TEDARIK_NOTU + " 1688 ve Taobao otomatik okunamaz; hücreye tıklayınca arama tarayıcınızda açılır.", NOT)
    s.birlestir("A2:K2", 40)
    s.satir(3, ["Ürün türü", "Çince adı", "Yurt dışı fiyatı", "Çin'de fabrika fiyatı (liste)", "En az sipariş", "Tedarikçi", "Fiyatın görüldüğü sayfa",
                "1688", "Taobao", "Ürün", "Bu türdeki ürünler"], SUTUN)
    gruplar = tedarik_gruplari(sonuc)
    for i, g in enumerate(gruplar, 4):
        b = dict((e.split(" (")[0], adres) for e, adres in g.baglantilar)
        h = lambda anahtar, etiket: _link(etiket, b[anahtar]) if anahtar in b else ""  # noqa: E731
        s.satir(i, [g.tur, g.cince_ad, g.yurtdisi, g.fiyat or "bakılamadı", g.moq, g.tedarikci, h("Tedarikçi sayfası", "Sayfayı aç"),
                    h("1688", "1688'de ara"), h("Taobao", "Taobao'da ara"), len(g.urunler), ", ".join(d.aday.ad for d in g.urunler)],
                [SARMA, DUZ, DUZ, DUZ, DUZ, SARMA, DUZ, DUZ, DUZ, TAM, SARMA])
    if not gruplar:
        s.yaz("A4", "Bu taramada Çin'deki fabrika fiyatı ve Çince ürün adı toplanmadı. “Ürünleri incele” sayfasındaki Alibaba, AliExpress, "
                    "Made-in-China ve Temu bağlantılarını kullanabilirsiniz.", NOT)
        s.birlestir("A4:K4", 28)
    return s


def _urun_linki(d: Degerlendirme):
    """Ürünün kendi sayfası; yoksa ürünün görsel araması. Satıcı ürünü tek tıkla görebilsin."""
    gor = inceleme_baglantilari(d.aday)["Ürünü gör"]
    sayfa = next((adres for etiket, adres in gor if etiket.startswith("Ürün sayfası")), None)
    return _link("Ürünü aç", sayfa) if sayfa else _link("Görsellere bak", dict(gor)["Görseller"])


def _cin_linki(d: Degerlendirme):
    """Çin'de tedarik araması: Çince adı varsa 1688, yoksa Alibaba."""
    cin = dict(inceleme_baglantilari(d.aday)["Çin'de tedarik"])
    if "1688" in cin:
        return _link("1688'de ara", cin["1688"])
    return _link("Alibaba'da ara", cin["Alibaba"]) if "Alibaba" in cin else ""


def _trendyol_linki(d: Degerlendirme):
    return _link("Trendyol'da ara", dict(inceleme_baglantilari(d.aday)["Türkiye'de bak"])["Trendyol"])


def yukselenler_sayfasi(sonuc: list[Degerlendirme]) -> Sayfa:
    s = Sayfa("Yükselenler", [5, 36, 14, 16, 16, 44, 12, 14, 22, 10, 10, 11, 70, 40, 50], dondur="C4")
    s.yaz("A1", "Yükselenler", AFIS)
    s.birlestir("A1:O1", 30)
    s.yaz("A2", "Yeni parlayan ürünler. “Ürünü aç” hücresine tıklayınca ürünün sayfası açılır. Yükseliş puanı: satışın ne kadarının son 30 güne "
                f"ait olduğu, satışın önceki aya göre artışı, son {YENI_GUN} günde ürünü anlatan yazılar ve arama ilgisinin yönü. {ESIK_YUKSELIS} ve "
                "üstü yükselen sayılır. “Yükseliş adayı” ürünlerde satış rakamı görülemedi; yükselişleri doğrulanmadı.", NOT)
    s.birlestir("A2:O2", 40)
    s.satir(3, ["#", "Ürün", "Ürün sayfası", "Çin'de tedarik", "Türkiye'de", "Listedeki adı", "Yurt dışı fiyatı", "Çin fiyatı", "Sınıf", "Yükseliş",
                "Kanıt", "Satış gücü",
                "Dayandığı rakamlar", "Görülemeyen", "Risk uyarıları"], SUTUN)
    liste = yukselenler(sonuc) + adaylar(sonuc)
    for i, d in enumerate(liste, 1):
        s.satir(i + 3, [i, d.aday.ad, _urun_linki(d), _cin_linki(d), _trendyol_linki(d), d.aday.orijinal_ad, d.aday.yurtdisi_fiyat,
                        d.aday.tedarik_fiyat, d.sinif, _p(d.yukselis),
                        d.yukselis.kanit, _p(d.satis), " ".join(d.yukselis.aciklamalar + d.satis.aciklamalar),
                        ", ".join(d.yukselis.eksikler), _risk(d)],
                [TAM, SARMA, DUZ, DUZ, DUZ, SARMA, DUZ, DUZ, DUZ, TAM, DUZ, TAM, SARMA, SARMA, SARMA])
    if not liste:
        s.yaz("A4", "Bu taramada yükselen sayılabilecek ürün çıkmadı.", NOT)
        s.birlestir("A4:O4")
    return s


def cok_satanlar_sayfasi(sonuc: list[Degerlendirme]) -> Sayfa:
    s = Sayfa("Çok satanlar", [5, 36, 14, 16, 16, 44, 12, 14, 22, 11, 10, 11, 16, 14, 12, 12, 14, 14, 50], dondur="C4")
    s.yaz("A1", "Çok Satanlar", AFIS)
    s.birlestir("A1:S1", 30)
    s.yaz("A2", "“Ürünü aç” hücresine tıklayınca ürünün sayfası açılır. Satış gücü puanı: satış sırası, 30 güne oranlanmış satış adedi, yorum "
                f"sayısı ve toplam satış adedi. {ESIK_SATIS} ve üstü çok satan sayılır.", NOT)
    s.birlestir("A2:S2")
    s.satir(3, ["#", "Ürün", "Ürün sayfası", "Çin'de tedarik", "Türkiye'de", "Listedeki adı", "Yurt dışı fiyatı", "Çin fiyatı", "Sınıf", "Satış gücü",
                "Kanıt", "Satış sırası",
                "30 günlük satış", "Toplam satış", "Yorum", "Yükseliş", "Ülke", "Veri tarihi", "Risk uyarıları"], SUTUN)
    liste = cok_satanlar(sonuc)
    for i, d in enumerate(liste, 1):
        a, aylik = d.aday, aylik_satis(d.aday)
        s.satir(i + 3, [i, a.ad, _urun_linki(d), _cin_linki(d), _trendyol_linki(d), a.orijinal_ad, a.yurtdisi_fiyat, a.tedarik_fiyat, d.sinif,
                        _p(d.satis), d.satis.kanit,
                        a.satis_sirasi, "" if aylik is None else round(aylik), a.toplam_satis, a.yorum, _p(d.yukselis), a.ulke,
                        _t(a.veri_tarihi), _risk(d)],
                [TAM, SARMA, DUZ, DUZ, DUZ, SARMA, DUZ, DUZ, DUZ, TAM, DUZ, TAM, TAM, TAM, TAM, TAM, DUZ, DUZ, SARMA])
    if not liste:
        s.yaz("A4", "Bu taramada çok satan sayılabilecek ürün çıkmadı.", NOT)
        s.birlestir("A4:S4")
    return s


def tum_urunler_sayfasi(sonuc: list[Degerlendirme], bugun: date) -> Sayfa:
    s = Sayfa("Tüm ürünler", [36, 22, 60, 11, 10, 12, 12, 10, 12, 12, 12, 12, 13, 13, 14, 12, 50, 40], dondur="B4")
    s.yaz("A1", "Tüm Ürünler ve Görülen Rakamlar", AFIS)
    s.birlestir("A1:R1", 30)
    s.yaz("A2", "Boş hücre, o rakamın hiçbir sayfada görülmediğini gösterir; tahmin edilmemiştir.", NOT)
    s.birlestir("A2:R2")
    s.satir(3, ["Ürün", "Sınıf", "Neden", "Satış gücü", "Yükseliş", "Satış sırası", "Son dönem satış", "Kaç gün", "Toplam satış", "Aylık değişim %", "Yorum",
                "İzlenme", "Arama ilgisi", "Güncel kaynak", "Ülke", "Veri tarihi", "Risk uyarıları", "Listedeki not"], SUTUN)
    for i, d in enumerate(sonuc, 4):
        a = d.aday
        s.satir(i, [a.ad, d.sinif, d.sinif_gerekce, _p(d.satis), _p(d.yukselis), a.satis_sirasi, a.son_satis, a.son_satis_gun,
                    a.toplam_satis, a.satis_degisim, a.yorum, a.izlenme, a.trend or "", guncel_kaynak_sayisi(a, bugun), a.ulke, _t(a.veri_tarihi),
                    _risk(d), a.aciklama],
                [SARMA, DUZ, SARMA, TAM, TAM, TAM, TAM, TAM, TAM, ONDALIK, TAM, TAM, DUZ, TAM, DUZ, DUZ, SARMA, SARMA])
    return s


def turkiye_sayfasi(sonuc: list[Degerlendirme], komisyon: float | None = None, kargo: float | None = None) -> Sayfa:
    s = Sayfa("Türkiye ve kâr", [36, 16, 16, 16, 16, 14, 16, 14, 16, 12, 44], dondur="B4")
    s.yaz("A1", "Türkiye Kontrolü ve Ürün Başına Kâr", AFIS)
    s.birlestir("A1:K1", 30)
    s.yaz("A2", "Sarı hücreleri siz doldurun. İlan sayısı: kendi pazaryerinizde ürünü aratınca ilk sayfada gerçekten aynı ürün olan ilan sayısı "
                f"(hiç yoksa 0). {AZ_SATICI} ilana kadar az satıcı, {ORTA_SATICI} ilana kadar orta, üstü kalabalık sayılır. "
                "Kâr = satış fiyatı − maliyet − komisyon − kargo; KDV, gelir vergisi, iade ve reklam gideri dahil değildir.", NOT)
    s.birlestir("A2:K2", 44)
    s.satir(3, ["Ürün", "Türkiye'de ilan sayısı", "Rekabet", "Satış fiyatı", "Toplam maliyet", "Komisyon", "Komisyon tutarı", "Kargo",
                "Ürün başına kâr", "Kâr marjı", "Not"], SUTUN)
    for i, d in enumerate(sonuc, 4):
        a, k = d.aday, d.kar
        oran = a.komisyon if a.komisyon is not None else komisyon
        gonderim = a.kargo if a.kargo is not None else kargo
        fiyat = a.satis_fiyati if a.satis_fiyati is not None else a.tr_fiyat
        dolu = f"AND(ISNUMBER(D{i}),ISNUMBER(E{i}))"
        notlar = []
        if a.tr_satici is not None and a.tr_kontrol != "satıcı":
            notlar.append("İlan sayısı asistanın tek sitede gördüğü kaba sayıdır; kendi pazaryerinizde bakıp düzeltin.")
        if a.satis_fiyati is None and a.tr_fiyat is not None:
            notlar.append("Satış fiyatı girilmedi; Türkiye'de görülen fiyat yazıldı.")
        if a.maliyet is None:
            notlar.append("Maliyeti yazınca kâr hesaplanır.")
        s.satir(i, [a.ad, "" if a.tr_satici is None else a.tr_satici,
                    Formul(f'IF(ISNUMBER(B{i}),IF(B{i}=0,"bulunamadı",IF(B{i}<={AZ_SATICI},"az satıcı",IF(B{i}<={ORTA_SATICI},"orta","kalabalık"))),"")',
                           "" if d.rekabet == "bilinmiyor" else d.rekabet),
                    "" if fiyat is None else fiyat, "" if a.maliyet is None else a.maliyet, "" if oran is None else oran / 100,
                    Formul(f'IF(ISNUMBER(D{i}),D{i}*F{i},"")', k.komisyon_tutari if k else ""), "" if gonderim is None else gonderim,
                    Formul(f'IF({dolu},D{i}-E{i}-G{i}-H{i},"")', k.net if k else ""),
                    Formul(f'IF({dolu},IF(D{i}>0,I{i}/D{i},""),"")', k.marj / 100 if k else ""), " ".join(notlar)],
                [SARMA, GIRDI_METIN, ETIKET, GIRDI_TL, GIRDI_TL, GIRDI_YUZDE, TL, GIRDI_TL, VURGU_TL, YUZDE, SARMA])
    n = len(sonuc) + 5
    s.yaz(f"A{n}", f"Bir ürünün öncelikli sayılması için: çok satan ya da yükselen olması, Türkiye'de sizin baktığınız pazaryerinde satanın "
                   f"olmaması ya da az olması, kâr marjının en az %{ONCELIK_MARJ:.0f} olması, yasaklı ya da izne bağlı ürün olmaması gerekir.", NOT)
    s.birlestir(f"A{n}:K{n}", 28)
    s.yaz(f"A{n + 1}", UYARI, NOT)
    s.birlestir(f"A{n + 1}:K{n + 1}", 40)
    return s


def kaynaklar_sayfasi(sonuc: list[Degerlendirme], bugun: date) -> Sayfa:
    s = Sayfa("Kaynaklar", [36, 20, 70, 14, 16], dondur="A4")
    s.yaz("A1", "Kaynaklar", AFIS)
    s.birlestir("A1:E1", 30)
    s.yaz("A2", f"Her ürünün görüldüğü sayfalar. Yayın tarihi yalnızca yazılar (haber, derleme) için yazılır; son {YENI_GUN} gün içindeyse güncel sayılır.", NOT)
    s.birlestir("A2:E2")
    s.satir(3, ["Ürün", "Tür", "Bağlantı", "Yayın tarihi", "Güncel mi"], SUTUN)
    n = 4
    for d in sonuc:
        a = d.aday
        for k, t in kaynak_ciftleri(a):
            guncel = "" if t is None or t > bugun else "evet" if (bugun - t).days <= YENI_GUN else "hayır"
            s.satir(n, [a.ad, "Yurt dışı", k, _t(t), guncel], [SARMA, DUZ, SARMA, DUZ, DUZ])
            n += 1
        for k in a.tr_kaynaklar:
            s.satir(n, [a.ad, "Türkiye", k, "", ""], [SARMA, DUZ, SARMA, DUZ, DUZ])
            n += 1
        if not a.kaynaklar:
            s.satir(n, [a.ad, "", "Kaynak bağlantısı yok", "", ""], [SARMA, DUZ, SARMA, DUZ, DUZ])
            n += 1
    return s


def dosya(sonuc: list[Degerlendirme], bugun: date, komisyon: float | None = None, kargo: float | None = None) -> bytes:
    return kitap_yaz([yukselenler_sayfasi(sonuc), cok_satanlar_sayfasi(sonuc), tedarik_sayfasi(sonuc), incele_sayfasi(sonuc), tum_urunler_sayfasi(sonuc, bugun),
                      turkiye_sayfasi(sonuc, komisyon, kargo), kaynaklar_sayfasi(sonuc, bugun)])
