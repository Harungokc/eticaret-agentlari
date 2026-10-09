"""Sonuçları Excel dosyasına döker: Özet, Konular, Talepler ve Yorumlar sayfaları.

"Yorumlar" sayfasında her yorum etiketleriyle durur; Excel'in süzgecini kullanarak örneğin yalnızca
kargo şikâyetlerini okuyabilirsiniz. Konular sayfasındaki sayılar o sayfadan formülle gelir.
"""

from __future__ import annotations

from analiz import Rapor, Yorum
from xlsx import AFIS, DUZ, ETIKET, NOT, ONDALIK, SARMA, SUTUN, TAM, YUZDE, Formul, Sayfa, kitap_yaz

Y = "'Yorumlar'"
UYARI = ("Bu analiz yalnızca verilen yorumları kapsar ve kelime eşleştirmesine dayanır; ironi, yazım hatası ve dolaylı anlatımı "
         "kaçırabilir. Sayıları, yanlarındaki alıntılarla birlikte değerlendirin. Araç herhangi bir pazaryeriyle bağlantılı değildir.")


def yorumlar_sayfasi(yorumlar: list[Yorum], r: Rapor) -> Sayfa:
    s = Sayfa("Yorumlar", [80, 8, 12, 44, 44, 9], dondur="A2")
    s.satir(1, ["Yorum", "Puan", "Genel", "Geçen konular", "Şikâyet edilen konular", "Talep"], SUTUN)
    for i, (y, e) in enumerate(zip(yorumlar, r.etiketler), 2):
        s.satir(i, [y.metin, y.puan, e["duygu"], ", ".join(e["konular"]), ", ".join(e["sikayet_konulari"]), "Evet" if e["talep"] else ""],
                [SARMA, TAM, DUZ, SARMA, SARMA, DUZ])
    return s


def ozet_sayfasi(r: Rapor) -> Sayfa:
    n = r.yorum_sayisi
    puan, genel, talep = (f"{Y}!{k}2:{k}{n + 1}" for k in "BCF")
    s = Sayfa("Özet", [34, 14, 14, 60])
    s.yaz("A1", "Yorum Analizi", AFIS)
    s.birlestir("A1:D1", 30)
    s.yaz("A2", "Sayılar “Yorumlar” sayfasından hesaplanır.", NOT)
    s.birlestir("A2:D2")
    s.satir(4, ["Genel", "Yorum", "Pay", "Açıklama"], SUTUN)
    s.satir(5, ["İncelenen yorum", Formul(f"COUNTA({Y}!A2:A{n + 1})", n), "", ""], [ETIKET, TAM, DUZ, NOT])
    s.satir(6, ["Ortalama puan", Formul(f'IF(COUNT({puan})>0,AVERAGE({puan}),"")', r.ortalama_puan if r.puanli else ""), "",
                f"Puanı verilen {r.puanli} yorum üzerinden."], [ETIKET, ONDALIK, DUZ, NOT])
    for no, (etiket, ad, adet) in enumerate((("Olumlu yorum", "olumlu", r.olumlu), ("Nötr yorum", "nötr", r.notr),
                                             ("Olumsuz yorum", "olumsuz", r.olumsuz)), 7):
        s.satir(no, [etiket, Formul(f'COUNTIF({genel},"{ad}")', adet), Formul(f"B{no}/B5", adet / n),
                     "Puan varsa puana göre (1–2 olumsuz, 3 nötr, 4–5 olumlu); yoksa kelimelere göre." if no == 7 else ""],
                [ETIKET, TAM, YUZDE, NOT])
    s.satir(10, ["Talep içeren yorum", Formul(f'COUNTIF({talep},"Evet")', r.talep_iceren_yorum), Formul("B10/B5", r.talep_iceren_yorum / n),
                 "“Keşke…”, “…olsaydı”, “tek eksiği…” gibi ifadeler geçen yorumlar."], [ETIKET, TAM, YUZDE, NOT])
    s.satir(12, ["Puan dağılımı", "Yorum", "Pay", ""], SUTUN)
    for no, yildiz in enumerate((5, 4, 3, 2, 1), 13):
        adet = r.puan_dagilimi[yildiz]
        s.satir(no, [f"{yildiz} yıldız", Formul(f"COUNTIF({puan},{yildiz})", adet),
                     Formul(f'IF(COUNT({puan})>0,B{no}/COUNT({puan}),"")', (adet / r.puanli) if r.puanli else "")], [ETIKET, TAM, YUZDE])
    no = 19
    for metin in r.uyarilar + [UYARI]:
        s.yaz(f"A{no}", metin, NOT)
        s.birlestir(f"A{no}:D{no}", 40)
        no += 1
    return s


def konular_sayfasi(r: Rapor) -> Sayfa:
    n = r.yorum_sayisi
    gecen, sikayet = f"{Y}!D2:D{n + 1}", f"{Y}!E2:E{n + 1}"
    s = Sayfa("Konular", [34, 14, 14, 14, 70])
    s.yaz("A1", "Müşteriler Neden Söz Ediyor", AFIS)
    s.birlestir("A1:E1", 30)
    s.yaz("A2", "Konular, şikâyeti en çok olandan başlayarak sıralanmıştır. Sayılar yorum adedidir.", NOT)
    s.birlestir("A2:E2")
    s.satir(4, ["Konu", "Söz eden yorum", "Şikâyet eden", "Şikâyet payı", "Yorumlardan örnek şikâyetler"], SUTUN)
    no = 5
    for k in r.konular:
        s.satir(no, [k.ad, Formul(f'COUNTIF({gecen},"*{k.ad}*")', k.yorum_sayisi), Formul(f'COUNTIF({sikayet},"*{k.ad}*")', k.sikayet),
                     Formul(f"IF(B{no}>0,C{no}/B{no},0)", k.sikayet / k.yorum_sayisi), "  |  ".join(k.sikayet_ornekleri)],
                [ETIKET, TAM, TAM, YUZDE, SARMA])
        no += 1
    no += 1
    if r.olumsuz_kelimeler:
        s.satir(no, ["Şikâyet ve taleplerde sık geçen kelimeler", "Yorum", "", "", ""], SUTUN)
        no += 1
        for kelime, adet in r.olumsuz_kelimeler:
            s.satir(no, [kelime, adet], [DUZ, TAM])
            no += 1
        no += 1
    s.yaz(f"A{no}", "Sık geçen kelimeler, hazır konu listesinde olmayan ürüne özgü sorunları (ör. “kapak”, “fermuar”) yakalamak içindir.", NOT)
    s.birlestir(f"A{no}:E{no}", 28)
    s.yaz(f"A{no + 1}", UYARI, NOT)
    s.birlestir(f"A{no + 1}:E{no + 1}", 40)
    return s


def talepler_sayfasi(r: Rapor) -> Sayfa:
    s = Sayfa("Talepler", [100, 44], dondur="A4")
    s.yaz("A1", "Müşteri Talepleri", AFIS)
    s.birlestir("A1:B1", 30)
    s.yaz("A2", "Yorumlarda “keşke”, “olsaydı”, “tek eksiği” gibi ifadelerle geçen cümleler. Ürünü geliştirmek için ilk bakılacak yer.", NOT)
    s.birlestir("A2:B2")
    s.satir(3, ["Yorumdan alıntı", "İlgili konu"], SUTUN)
    no = 4
    for cumle, konular in r.talepler:
        s.satir(no, [cumle, ", ".join(konular)], [SARMA, SARMA])
        no += 1
    if not r.talepler:
        s.yaz("A4", "Bu yorumlarda açık bir talep ifadesi bulunamadı.", NOT)
        no = 5
    if r.konusuz_sikayetler:
        no += 1
        s.satir(no, ["Hazır konulara girmeyen şikâyetler", ""], SUTUN)
        no += 1
        for cumle in r.konusuz_sikayetler:
            s.satir(no, [cumle, ""], [SARMA, DUZ])
            no += 1
    return s


def dosya(yorumlar: list[Yorum], r: Rapor) -> bytes:
    return kitap_yaz([ozet_sayfasi(r), konular_sayfasi(r), talepler_sayfasi(r), yorumlar_sayfasi(yorumlar, r)])
