"""Sonuçları Excel dosyasına döker: Özet, Öneriler, Ürünler (ya da Kampanyalar) ve varsa Arama terimleri sayfaları.

Oranlar formülle yazılır; satıcı bir hücreyi değiştirince (ör. sipariş başına kâr) sonuç yeniden hesaplanır.
"""

from __future__ import annotations

from analiz import EN_AZ_SIPARIS, EN_AZ_TIKLAMA, Kalem, Rapor
from xlsx import AFIS, DUZ, ETIKET, GIRDI_METIN, GIRDI_TL, NOT, ONDALIK, SARMA, SUTUN, TAM, TL, YUZDE, Formul, Sayfa, kitap_yaz
from yonetim import Yonetim, is_adi

ONCELIK = {1: "Hemen", 2: "Bu hafta", 3: "İzle"}

UYARI = ("Bu analiz yalnızca verilen reklam raporunu kapsar. Panelin gösterdiği reklam satışı, reklam olmasa da gelecek "
         "satışları ayırmaz; reklam getirisi gerçek etkiden yüksek görünebilir. Araç herhangi bir pazaryeriyle bağlantılı değildir.")


def _yz(x: float | None) -> float | str:
    return "" if x is None else x / 100


def ozet_sayfasi(r: Rapor) -> Sayfa:
    s = Sayfa("Özet", [44, 20])
    s.yaz("A1", "Reklam Analizi", AFIS)
    s.birlestir("A1:B1", 30)
    s.satir(3, ["Genel", "Değer"], SUTUN)
    satirlar = [("Reklam harcaması", r.harcama, TL), ("Reklamdan gelen satış", r.ciro if r.ciro is not None else "", TL),
                ("Reklam getirisi (ROAS: satış ÷ harcama)", r.roas if r.roas is not None else "", ONDALIK),
                ("Reklam maliyet oranı (harcama ÷ satış)", _yz(r.acos), YUZDE),
                ("Sipariş", r.siparis if r.siparis is not None else "", TAM),
                ("Tıklama", r.tiklama if r.tiklama is not None else "", TAM),
                ("Gösterim", r.gosterim if r.gosterim is not None else "", TAM),
                ("Tıklama oranı", _yz(r.ctr), YUZDE), ("Dönüşüm oranı (sipariş ÷ tıklama)", _yz(r.cvr), YUZDE),
                ("Tıklama başı maliyet", r.tbm if r.tbm is not None else "", TL),
                ("Satış getirmeyen harcama", r.satis_getirmeyen_harcama, TL)]
    if r.maliyet_var:
        satirlar.append(("Reklam sonrası kalan (maliyeti bilinen kalemler)", r.net if r.net is not None else "", TL))
    for no, (ad, deger, bicem) in enumerate(satirlar, 4):
        s.satir(no, [ad, deger], [ETIKET, bicem])
    no = 5 + len(satirlar)
    for metin in [UYARI] + r.uyarilar:
        s.yaz(f"A{no}", metin, NOT)
        s.birlestir(f"A{no}:B{no}", 42)
        no += 1
    return s


def oneriler_sayfasi(r: Rapor) -> Sayfa:
    s = Sayfa("Öneriler", [6, 12, 46, 60, 60], dondur="A2")
    s.satir(1, ["No", "Konu", "Başlık", "Bulgu", "Öneri"], SUTUN)
    for no, o in enumerate(r.oneriler, 1):
        s.satir(no + 1, [no, o.tur, o.baslik, o.bulgu, o.oneri], [TAM, DUZ, SARMA, SARMA, SARMA])
    if not r.oneriler:
        s.yaz("A2", "Bu raporda kural eşiklerini aşan bir bulgu çıkmadı.", NOT)
    return s


def kalem_sayfasi(ad: str, baslik: str, kalemler: list[Kalem], r: Rapor, kar: bool) -> Sayfa:
    basliklar = [baslik, "Kampanya", "Harcama", "Satış", "Sipariş", "Tıklama", "Gösterim", "ROAS", "Reklam maliyet oranı",
                 "Tıklama oranı", "Dönüşüm", "Tıklama başı maliyet", "Durum"]
    genislik = [40, 22, 14, 14, 10, 10, 12, 8, 12, 10, 10, 12, 14]
    if kar:
        basliklar += ["Sipariş başına kâr (reklam öncesi)", "Başa baş oran", "Reklam sonrası kalan"]
        genislik += [16, 12, 16]
    s = Sayfa(ad, genislik, dondur="A2")
    s.satir(1, basliklar, SUTUN)
    for no, k in enumerate(kalemler, 2):
        d = lambda x: x if x is not None else ""  # noqa: E731
        s.satir(no, [k.ad, k.kampanya, k.harcama, d(k.ciro), d(k.siparis), d(k.tiklama), d(k.gosterim),
                     Formul(f'IF(C{no}>0,D{no}/C{no},"")', k.roas if k.roas is not None else ""),
                     Formul(f'IF(D{no}>0,C{no}/D{no},"")', _yz(k.acos)),
                     Formul(f'IF(G{no}>0,F{no}/G{no},"")', _yz(k.ctr)),
                     Formul(f'IF(F{no}>0,E{no}/F{no},"")', _yz(k.cvr)),
                     Formul(f'IF(F{no}>0,C{no}/F{no},"")', k.tbm if k.tbm is not None else ""),
                     k.durum],
                [SARMA, SARMA, TL, TL, TAM, TAM, TAM, ONDALIK, YUZDE, YUZDE, YUZDE, TL, DUZ])
        if kar:
            s.satir(no, [d(k.birim_kar),
                         Formul(f'IF(AND(D{no}>0,E{no}>0,N{no}<>""),N{no}/(D{no}/E{no}),"")', _yz(k.basa_bas_acos)),
                         Formul(f'IF(N{no}<>"",E{no}*N{no}-C{no},"")', k.net if k.net is not None else "")],
                    [GIRDI_TL, YUZDE, TL], bas=14)
    son = len(kalemler) + 3
    notlar = [f"Durum: \"Satış yok\" en az {EN_AZ_TIKLAMA} tıklama alıp satış getirmeyen; \"Az veri\" {EN_AZ_SIPARIS} siparişten az olan kalem."]
    if kar:
        notlar.append("Sarı hücreler değiştirilebilir: sipariş başına kâr = satış fiyatı − ürün maliyeti − komisyon − kargo. "
                      "Başa baş oran: reklam maliyet oranı bunun üstündeyse reklam zarar ettirir.")
    for i, n in enumerate(notlar):
        s.yaz(f"A{son + i}", n, NOT)
        s.birlestir(f"A{son + i}:M{son + i}", 30)
    return s


def yapilacaklar_sayfasi(y: Yonetim) -> Sayfa:
    s = Sayfa("Yapılacaklar", [36, 14, 10, 22, 14, 14, 13, 60, 60, 12], dondur="A2")
    s.satir(1, ["Reklam", "Tür", "Öncelik", "İş", "Dönem harcaması", "Önerilen harcama", "Günlük bütçe", "Neden", "Beklenen",
                "Yapıldı mı?"], SUTUN)
    for no, x in enumerate(y.eylemler, 2):
        yeni = x.harcama if x.yeni_harcama is None else x.yeni_harcama
        gun = Formul(f"F{no}/{y.gun}", yeni / y.gun) if y.gun else ""
        s.satir(no, [x.hedef, x.tur, ONCELIK[x.oncelik], is_adi(x), x.harcama, yeni, gun, x.neden, x.beklenen, ""],
                [SARMA, DUZ, DUZ, DUZ, TL, TL, TL, SARMA, SARMA, GIRDI_METIN])
    son = len(y.eylemler) + 1
    alt = son + 2
    s.satir(alt, ["Toplam", "", "", "", Formul(f"SUM(E2:E{son})", y.harcama), Formul(f"SUM(F2:F{son})", y.yeni_harcama)],
            [ETIKET, DUZ, DUZ, DUZ, TL, TL])
    s.yaz(f"A{alt + 2}", "Araç hiçbir ayarı değiştirmez; işleri panelde siz yaparsınız. Yaptığınız işin karşısına \"Evet\" yazın. "
                         "Önerilen harcama aynı uzunlukta bir dönem içindir"
                         + (f"; günlük bütçe = önerilen harcama ÷ {y.gun} gün." if y.gun else ".")
                         + " Arama terimi raporunda toplam terimlerden hesaplanır.", NOT)
    s.birlestir(f"A{alt + 2}:J{alt + 2}", 30)
    return s


def takip_sayfasi(y: Yonetim) -> Sayfa:
    s = Sayfa("Takip", [36, 14, 22, 20, 12, 44, 44, 70], dondur="A2")
    s.satir(1, ["Reklam", "Tür", "Geçen dönemin işi", "Yapıldı mı", "Sonuç", "Geçen dönem", "Bu dönem", "Ayrıntı"], SUTUN)
    for no, t in enumerate(y.takip, 2):
        s.satir(no, [t.hedef, t.tur, t.is_, t.yapildi, t.sonuc, t.once, t.simdi, t.yorum],
                [SARMA, DUZ, DUZ, DUZ, DUZ, SARMA, SARMA, SARMA])
    alt = len(y.takip) + 3
    s.yaz(f"A{alt}", "\"Yapıldı mı\" rapordaki rakamlardan çıkarılır; araç panel ayarlarını görmez. İki rapor aynı uzunlukta dönemi "
                     "kapsamalıdır.", NOT)
    s.birlestir(f"A{alt}:H{alt}", 30)
    return s


def dosya(r: Rapor, y: Yonetim | None = None) -> bytes:
    sayfalar = [ozet_sayfasi(r)]
    if y is not None:
        sayfalar.append(yapilacaklar_sayfasi(y))
        if y.takip:
            sayfalar.append(takip_sayfasi(y))
    sayfalar.append(oneriler_sayfasi(r))
    if r.kalemler:
        ad = "Ürünler" if r.birim == "Ürün" else "Kampanyalar"
        sayfalar.append(kalem_sayfasi(ad, r.birim, r.kalemler, r, kar=r.maliyet_var))
    if r.terimler:
        sayfalar.append(kalem_sayfasi("Arama terimleri", "Arama terimi", r.terimler, r, kar=False))
    return kitap_yaz(sayfalar)
