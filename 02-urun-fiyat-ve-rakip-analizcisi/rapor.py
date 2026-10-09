"""Sonuçları Excel dosyasına döker.

Dosya dört sayfadan oluşur: Özet, Konum, Rakipler ve Ürünler. Özet ve Konum sayfalarındaki rakamlar
"Ürünler" sayfasından formülle gelir; Konum sayfasındaki sarı fiyat hücresi değiştirildiğinde
sıralama ve farklar yeniden hesaplanır.
"""

from __future__ import annotations

from analiz import YAKIN_ORAN, Konum, Ozet, RakipRaporu, Urun
from xlsx import (AFIS, DUZ, ETIKET, GIRDI_TL, NOT, ONDALIK, SARMA, SUTUN, TAM, TL, VURGU_TL, YUZDE, Formul, Sayfa,
                  kitap_yaz)

URUNLER = "'Ürünler'"
UYARI = ("Bu analiz yalnızca listedeki ürünleri kapsar. Satış adedi ve ciro bilgisi içermez; yorum ve favori sayısı "
         "ilginin dolaylı göstergesidir. Araç herhangi bir pazaryeriyle bağlantılı değildir.")


def _kargo(u: Urun) -> str:
    return "" if u.kargo_ucretsiz is None else ("Ücretsiz" if u.kargo_ucretsiz else "Ücretli")


def urunler_sayfasi(pazar: list[Urun]) -> Sayfa:
    s = Sayfa("Ürünler", [44, 20, 14, 9, 12, 12, 12], dondur="A2")
    s.satir(1, ["Ürün", "Marka", "Fiyat", "Puan", "Yorum", "Favori", "Kargo"], SUTUN)
    for i, u in enumerate(pazar, 2):
        s.satir(i, [u.ad, u.marka, u.fiyat, u.puan, u.yorum, u.favori, _kargo(u)], [SARMA, DUZ, TL, ONDALIK, TAM, TAM, DUZ])
    return s


def _alan(sutun: str, n: int) -> str:
    return f"{URUNLER}!{sutun}2:{sutun}{n + 1}"


def ozet_sayfasi(o: Ozet) -> Sayfa:
    n = o.urun_sayisi
    fiyat, puan, yorum, favori = (_alan(k, n) for k in "CDEF")
    s = Sayfa("Özet", [34, 18, 62])
    s.yaz("A1", "Ürün Ortalamaları", AFIS)
    s.birlestir("A1:C1", 30)
    s.yaz("A2", "Rakamlar “Ürünler” sayfasındaki listeden hesaplanır; listeyi değiştirirseniz güncellenir.", NOT)
    s.birlestir("A2:C2")
    satirlar = [
        ("Fiyat", None, None, None),
        ("İncelenen ürün sayısı", Formul(f"COUNT({fiyat})", n), TAM, ""),
        ("Ortalama fiyat", Formul(f"AVERAGE({fiyat})", o.fiyat.ortalama), TL, "Çok pahalı ya da çok ucuz birkaç ürün ortalamayı kaydırabilir."),
        ("Ortanca fiyat", Formul(f"MEDIAN({fiyat})", o.fiyat.ortanca), VURGU_TL, "Ürünlerin yarısı bu fiyatın altında, yarısı üstünde."),
        ("En düşük fiyat", Formul(f"MIN({fiyat})", o.fiyat.en_az), TL, ""),
        ("Alt çeyrek", Formul(f"QUARTILE({fiyat},1)", o.alt_ceyrek), TL, "Ürünlerin dörtte biri bu fiyatın altında."),
        ("Üst çeyrek", Formul(f"QUARTILE({fiyat},3)", o.ust_ceyrek), TL, "Ürünlerin dörtte biri bu fiyatın üstünde."),
        ("En yüksek fiyat", Formul(f"MAX({fiyat})", o.fiyat.en_cok), TL, ""),
        ("Yorum ağırlıklı ortalama fiyat",
         Formul(f"IF(SUM({yorum})>0,SUMPRODUCT({fiyat},{yorum})/SUM({yorum}),\"\")", o.yorum_agirlikli_fiyat if o.yorum_agirlikli_fiyat is not None else ""),
         TL, "Yorumu çok olan ürünlerin fiyatına daha çok ağırlık verir; ilginin toplandığı fiyat düzeyini gösterir."),
        ("İlgi", None, None, None),
        ("Ortalama puan", Formul(f"IF(COUNT({puan})>0,AVERAGE({puan}),\"\")", o.puan.ortalama if o.puan.adet else ""), ONDALIK,
         f"Puanı bilinen {o.puan.adet} ürün üzerinden."),
        ("Ortanca yorum sayısı", Formul(f"IF(COUNT({yorum})>0,MEDIAN({yorum}),\"\")", o.yorum.ortanca if o.yorum.adet else ""), TAM,
         f"Yorum sayısı bilinen {o.yorum.adet} ürün üzerinden."),
        ("Ortalama yorum sayısı", Formul(f"IF(COUNT({yorum})>0,AVERAGE({yorum}),\"\")", o.yorum.ortalama if o.yorum.adet else ""), TAM, ""),
        ("Ortanca favori sayısı", Formul(f"IF(COUNT({favori})>0,MEDIAN({favori}),\"\")", o.favori.ortanca if o.favori.adet else ""), TAM,
         f"Favori sayısı bilinen {o.favori.adet} ürün üzerinden."),
        ("Ücretsiz kargolu ürün oranı", (o.ucretsiz_kargo_orani / 100) if o.ucretsiz_kargo_orani is not None else "", YUZDE,
         f"Kargo bilgisi olan {o.kargo_bilinen} ürün üzerinden."),
    ]
    no = 4
    for etiket, deger, bicem, aciklama in satirlar:
        if deger is None:
            no += 1 if no > 4 else 0
            s.satir(no, [etiket, "Değer", "Açıklama"], SUTUN)
        else:
            s.satir(no, [etiket, deger, aciklama], [ETIKET, bicem, NOT])
        no += 1
    no += 1
    for metin in o.uyarilar + [UYARI]:
        s.yaz(f"A{no}", metin, NOT)
        s.birlestir(f"A{no}:C{no}", 28)
        no += 1
    return s


def konum_sayfasi(k: Konum) -> Sayfa:
    fiyat = _alan("C", k.urun_sayisi)
    s = Sayfa("Konum", [34, 18, 18, 18, 22])
    s.yaz("A1", "Fiyat Konumu", AFIS)
    s.birlestir("A1:E1", 30)
    s.yaz("A2", "Sarı hücredeki fiyatı değiştirin; sıralama ve farklar yeniden hesaplanır.", NOT)
    s.birlestir("A2:E2")
    s.satir(4, ["Sizin fiyatınız", k.fiyat], [ETIKET, GIRDI_TL])
    s.satir(6, ["Pazardaki yeriniz", "Değer"], SUTUN)
    s.satir(7, ["Karşılaştırılan ürün sayısı", Formul(f"COUNT({fiyat})", k.urun_sayisi)], [ETIKET, TAM])
    s.satir(8, ["Sizden ucuz ürün", Formul(f'COUNTIF({fiyat},"<"&B4)', k.daha_ucuz)], [ETIKET, TAM])
    s.satir(9, ["Aynı fiyatlı ürün", Formul(f"COUNTIF({fiyat},B4)", k.ayni)], [ETIKET, TAM])
    s.satir(10, ["Sizden pahalı ürün", Formul(f'COUNTIF({fiyat},">"&B4)', k.daha_pahali)], [ETIKET, TAM])
    s.satir(11, ["Fiyat sıranız (0 = en ucuz, 100 = en pahalı)", Formul("(B8+B9/2)/B7*100", k.yuzdelik)], [ETIKET, ONDALIK])
    s.satir(12, ["Pazarın ortanca fiyatı", Formul(f"MEDIAN({fiyat})", k.ortanca)], [ETIKET, VURGU_TL])
    s.satir(13, ["Ortancadan farkınız", Formul("(B4-B12)/B12", k.ortancadan_fark / 100)], [ETIKET, YUZDE])
    s.satir(14, ["Ana fiyat aralığı — alt (alt çeyrek)", Formul(f"QUARTILE({fiyat},1)", k.ana_aralik[0])], [ETIKET, TL])
    s.satir(15, ["Ana fiyat aralığı — üst (üst çeyrek)", Formul(f"QUARTILE({fiyat},3)", k.ana_aralik[1])], [ETIKET, TL])
    s.satir(16, ["Ana aralığın içinde misiniz?", Formul('IF(AND(B4>=B14,B4<=B15),"Evet","Hayır")', "Evet" if k.ana_aralikta else "Hayır")],
            [ETIKET, DUZ])
    oran = int(YAKIN_ORAN * 100)
    s.satir(17, [f"Benzer fiyatlı ürün (±%{oran})",
                 Formul(f'COUNTIFS({fiyat},">="&B4*{1 - YAKIN_ORAN},{fiyat},"<="&B4*{1 + YAKIN_ORAN})', k.yakin_sayisi)], [ETIKET, TAM])
    s.satir(19, ["Fiyat dilimi (ürünler dört eşit gruba bölünür)", "En düşük", "En yüksek", "Ürün sayısı", "Ortanca yorum sayısı"], SUTUN)
    no = 20
    for i, d in enumerate(k.dilimler, 1):
        etiket = f"{i}. dilim" + ("  ← en çok ilgi gören" if k.ilgi_goren is d else "")
        s.satir(no, [etiket, d.alt, d.ust, d.urun_sayisi, d.ortanca_yorum], [ETIKET, TL, TL, TAM, TAM])
        no += 1
    no += 1
    notlar = ["Dilim tablosu dosya oluşturulurken yazılmıştır; listeyi değiştirirseniz güncellenmez.",
              "“En çok ilgi gören” dilim, ortanca yorum sayısı en yüksek olan dilimdir; satış adedini göstermez."]
    for metin in notlar + k.uyarilar + [UYARI]:
        s.yaz(f"A{no}", metin, NOT)
        s.birlestir(f"A{no}:E{no}", 28)
        no += 1
    return s


def rakip_sayfasi(r: RakipRaporu) -> Sayfa:
    s = Sayfa("Rakipler", [40, 18, 16, 10, 12, 12, 12])
    s.yaz("A1", "Rakip Karşılaştırması", AFIS)
    s.birlestir("A1:G1", 30)
    s.yaz("A2", f"Ürününüz {r.rakip_sayisi} rakiple karşılaştırıldı. Tabloda fiyatı size en yakın {len(r.rakipler)} rakip yer alır.", NOT)
    s.birlestir("A2:G2")
    s.satir(4, ["Ürün", "Marka", "Fiyat", "Puan", "Yorum", "Favori", "Kargo"], SUTUN)
    b = r.benim
    s.satir(5, ["Sizin ürününüz: " + b.ad, b.marka, b.fiyat, b.puan, b.yorum, b.favori, _kargo(b)],
            [ETIKET, ETIKET, VURGU_TL, ONDALIK, TAM, TAM, DUZ])
    no = 6
    for u in r.rakipler:
        s.satir(no, [u.ad, u.marka, u.fiyat, u.puan, u.yorum, u.favori, _kargo(u)], [SARMA, DUZ, TL, ONDALIK, TAM, TAM, DUZ])
        no += 1
    no += 1
    s.satir(no, ["Ölçü", "Sizin ürününüz", "Rakip ortancası", "Sıranız", "Durum", "", ""], SUTUN)
    no += 1
    for k in r.kiyaslar:
        sira = f"{k.sira}/{k.kac_urun}" if k.sira else ""
        s.satir(no, [k.olcu, k.benim, k.rakip_ortancasi, sira, k.durum], [ETIKET, DUZ, DUZ, DUZ, ETIKET])
        no += 1
    no += 1
    ozetler = ["Öne geçtiğiniz noktalar: " + (", ".join(r.onde) if r.onde else "yok"),
               "Geride kaldığınız noktalar: " + (", ".join(r.geride) if r.geride else "yok"),
               "“Önde/geride”, rakiplerin ortancasına göre belirlenir. Bu sayfadaki değerler dosya oluşturulurken yazılmıştır."]
    for metin in ozetler + r.uyarilar + [UYARI]:
        s.yaz(f"A{no}", metin, NOT)
        s.birlestir(f"A{no}:G{no}", 28)
        no += 1
    return s


def dosya(pazar: list[Urun], o: Ozet, k: Konum | None, r: RakipRaporu | None) -> bytes:
    sayfalar = [ozet_sayfasi(o)]
    if k:
        sayfalar.append(konum_sayfasi(k))
    if r:
        sayfalar.append(rakip_sayfasi(r))
    sayfalar.append(urunler_sayfasi(pazar))
    return kitap_yaz(sayfalar)
