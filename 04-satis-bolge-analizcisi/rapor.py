"""Sonuçları Excel dosyasına döker: Özet, İller, Bölgeler, İlçeler ve Siparişler sayfaları.

"Siparişler" sayfasına yalnızca il, bölge, ilçe, tutar, ürün ve durum yazılır; kişisel bilgi yazılmaz.
"""

from __future__ import annotations

from analiz import IL_BOLGESI, Rapor, Satir, Siparis, baslik
from xlsx import AFIS, DUZ, ETIKET, NOT, SARMA, SUTUN, TAM, TL, YUZDE, Formul, Sayfa, kitap_yaz

UYARI = ("Bu analiz yalnızca verilen sipariş listesini kapsar. İl ve ilçe, listedeki teslimat bilgisinden alınır; müşteri adı, "
         "telefon ve açık adres kullanılmaz. Araç herhangi bir pazaryeriyle bağlantılı değildir.")


def _tablo(s: Sayfa, bas: int, baslik_adi: str, satirlar: list[Satir], r: Rapor, bolge: bool = False, urun: bool = False) -> int:
    basliklar = [baslik_adi] + (["Bölge"] if bolge else []) + ["Sipariş", "Sipariş payı"]
    if r.ciro is not None:
        basliklar += ["Ciro", "Ciro payı", "Ortalama sepet"]
    if r.iade_bilgisi_var:
        basliklar += ["İade", "İade oranı"]
    if urun and r.urun_bilgisi_var:
        basliklar += ["En çok satan ürün"]
    s.satir(bas, basliklar, SUTUN)
    son = bas + len(satirlar)
    kol = 3 if bolge else 2  # sipariş sütunu
    harf = "ABCDEFGHIJ"
    for no, x in enumerate(satirlar, bas + 1):
        degerler, bicemler = [x.ad] + ([x.bolge] if bolge else []), [ETIKET] + ([DUZ] if bolge else [])
        degerler += [x.siparis, Formul(f"{harf[kol - 1]}{no}/{r.siparis_sayisi}", x.pay / 100)]
        bicemler += [TAM, YUZDE]
        if r.ciro is not None:
            degerler += [x.ciro, (x.ciro_payi / 100) if x.ciro_payi is not None else "",
                         Formul(f"IF({harf[kol - 1]}{no}>0,{harf[kol + 1]}{no}/{harf[kol - 1]}{no},0)", x.ortalama_sepet or 0)]
            bicemler += [TL, YUZDE, TL]
        if r.iade_bilgisi_var:
            degerler += [x.iade, (x.iade_orani / 100) if x.iade_orani is not None else ""]
            bicemler += [TAM, YUZDE]
        if urun and r.urun_bilgisi_var:
            degerler += [x.en_cok_satan]
            bicemler += [SARMA]
        s.satir(no, degerler, bicemler)
    return son + 1


def ozet_sayfasi(r: Rapor) -> Sayfa:
    s = Sayfa("Özet", [36, 18, 16, 16, 18, 16, 16, 12, 12])
    s.yaz("A1", "Satış Bölge Analizi", AFIS)
    s.birlestir("A1:I1", 30)
    s.satir(3, ["Genel", "Değer"], SUTUN)
    s.satir(4, ["Sipariş sayısı", r.siparis_sayisi], [ETIKET, TAM])
    s.satir(5, ["Toplam ciro", r.ciro if r.ciro is not None else ""], [ETIKET, TL])
    s.satir(6, ["Sipariş gelen il sayısı (81 il içinde)", r.il_sayisi], [ETIKET, TAM])
    s.satir(7, ["İlk 3 ilin sipariş payı", r.ilk3_pay / 100], [ETIKET, YUZDE])
    s.satir(8, ["İlk 10 ilin sipariş payı", r.ilk10_pay / 100], [ETIKET, YUZDE])
    no = _tablo(s, 10, "Bölge", r.bolgeler, r)
    no = _tablo(s, no + 1, "En çok sipariş gelen 10 il", r.iller[:10], r, bolge=True)
    no += 1
    if r.siparis_gelmeyen_iller:
        s.yaz(f"A{no}", f"Sipariş gelmeyen iller ({len(r.siparis_gelmeyen_iller)}): " + ", ".join(r.siparis_gelmeyen_iller), NOT)
        s.birlestir(f"A{no}:I{no}", 42)
        no += 1
    for metin in r.uyarilar + ["Tablolardaki değerler dosya oluşturulurken yazılmıştır.", UYARI]:
        s.yaz(f"A{no}", metin, NOT)
        s.birlestir(f"A{no}:I{no}", 28)
        no += 1
    return s


def liste_sayfasi(ad: str, baslik_metni: str, sutun_adi: str, satirlar: list[Satir], r: Rapor, bolge: bool) -> Sayfa:
    s = Sayfa(ad, [34, 20, 14, 14, 18, 14, 16, 12, 12, 40] if bolge else [38, 14, 14, 18, 14, 16, 12, 12, 40], dondur="A4")
    s.yaz("A1", baslik_metni, AFIS)
    s.birlestir("A1:H1", 30)
    _tablo(s, 3, sutun_adi, satirlar, r, bolge=bolge, urun=True)
    return s


def siparisler_sayfasi(siparisler: list[Siparis]) -> Sayfa:
    s = Sayfa("Siparişler", [22, 22, 24, 16, 44, 12], dondur="A2")
    s.satir(1, ["İl", "Bölge", "İlçe", "Tutar", "Ürün", "Durum"], SUTUN)
    no = 2
    for x in siparisler:
        if x.iptal or not x.il:
            continue
        s.satir(no, [x.il, IL_BOLGESI[x.il], baslik(x.ilce) if x.ilce else "", x.tutar, x.urun, "İade" if x.iade else ""],
                [DUZ, DUZ, DUZ, TL, SARMA, DUZ])
        no += 1
    return s


def dosya(siparisler: list[Siparis], r: Rapor) -> bytes:
    return kitap_yaz([ozet_sayfasi(r), liste_sayfasi("İller", "İl Bazında Satışlar", "İl", r.iller, r, True),
                      liste_sayfasi("İlçeler", "En Çok Sipariş Gelen İlçeler", "İl / İlçe", r.ilceler, r, False),
                      siparisler_sayfasi(siparisler)])
