"""Çalıştırmak için: python -m unittest -v"""

import contextlib
import io
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path
from xml.dom import minidom

from agent import main as _main
from analiz import Maliyet, ReklamSatiri, analiz_et, anahtar
from okuyucu import OkumaHatasi, maliyet_oku, oku, sade, sayi, sutunlari_goster
from rapor import dosya
from rapor_html import sayfa
from xlsx import Sayfa, kitap_yaz
from yonetim import ARTIR, AYIR, DOKUNMA, DURDUR, NEGATIF, TEKLIF, gunluk, yonet

KLASOR = Path(__file__).parent / "ornek"
URUN = str(KLASOR / "ornek_urun_reklami.csv")
TERIM = str(KLASOR / "ornek_arama_terimleri.csv")
MALIYET = str(KLASOR / "ornek_maliyetler.csv")


def main(argv):
    cikti, hata = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        kod = _main(argv)
    return kod, cikti.getvalue(), hata.getvalue()


def yaz(icerik: str, ad: str = "rapor.csv") -> str:
    d = tempfile.mkdtemp()
    yol = Path(d) / ad
    yol.write_text(icerik, encoding="utf-8")
    return str(yol)


class Sayilar(unittest.TestCase):
    def test_bicimler(self):
        self.assertEqual(sayi("1.234,56 TL"), 1234.56)
        self.assertEqual(sayi("1,234.56"), 1234.56)
        self.assertEqual(sayi("459,90"), 459.9)
        self.assertEqual(sayi("12.500"), 12500)
        self.assertEqual(sayi("%20"), 20)
        self.assertEqual(sayi(3.5), 3.5)
        self.assertIsNone(sayi(""))
        self.assertIsNone(sayi("-"))

    def test_sutun_adi_sadelesir(self):
        self.assertEqual(sade("7 Günlük Toplam Satış (₺)"), "7 gunluk toplam satis")
        self.assertEqual(sade("  HARCAMA (TL) "), "harcama")
        self.assertEqual(anahtar("Çelik Termos 750 ml"), anahtar("ÇELİK  termos 750ML"))


class Okuma(unittest.TestCase):
    def test_ornek_urun_raporu(self):
        s = oku(URUN)
        self.assertEqual(len(s), 12)
        self.assertEqual(s[0].urun, "Çelik Termos 750 ml")
        self.assertEqual(s[0].harcama, 4350)
        self.assertEqual(s[0].ciro, 28513.8)

    def test_amazon_bicimi_arama_terimi(self):
        s = oku(TERIM)
        self.assertEqual(s[0].terim, "çelik termos")
        self.assertEqual(s[0].siparis, 31)
        self.assertEqual(s[0].ciro, 14254.2)

    def test_baslik_ustunde_aciklama_satiri(self):
        yol = yaz("Mağaza reklam raporu;;\n01.09.2026 - 30.09.2026;;\nÜrün;Harcama;Satış\nA;100;300\n")
        s = oku(yol)
        self.assertEqual((s[0].urun, s[0].harcama, s[0].ciro), ("A", 100, 300))

    def test_toplam_satiri_atlanir(self):
        s = oku(yaz("Ürün;Harcama;Satış\nA;100;300\nB;50;0\nToplam;150;300\n"))
        self.assertEqual(len(s), 2)

    def test_platform_sutunlari(self):
        # Meta: bağlantı tıklaması, tüm tıklamalardan önce alınır
        _, e = sutunlari_goster(yaz("Reklam Adı;Harcanan Tutar;Tıklamalar (Tümü);Bağlantı Tıklamaları;Gösterimler;Alışverişler\nA;1;9;4;100;1\n"))
        self.assertEqual((e["tiklama"], e["harcama"], e["siparis"]), ("Bağlantı Tıklamaları", "Harcanan Tutar", "Alışverişler"))
        # Google/TikTok Türkçe: "Maliyet" harcamadır, "Görüntülemeler" gösterimdir
        _, e = sutunlari_goster(yaz("Kampanya;Maliyet;Görüntülemeler;Tıklamalar;Dönüşümler;Dönüşüm değeri\nA;1;100;5;1;50\n"))
        self.assertEqual((e["harcama"], e["gosterim"], e["siparis"], e["ciro"]), ("Maliyet", "Görüntülemeler", "Dönüşümler", "Dönüşüm değeri"))

    def test_elle_esleme(self):
        yol = yaz("Ürün;Harcanan Para;Reklamdan Kazanç\nA;100;300\n")
        with self.assertRaises(OkumaHatasi) as h:
            oku(yol)
        self.assertIn("Harcanan Para", str(h.exception))  # hata mesajı dosyadaki sütunları gösterir
        s = oku(yol, {"harcama": "Harcanan Para", "ciro": "Reklamdan Kazanç"})
        self.assertEqual((s[0].harcama, s[0].ciro), (100, 300))

    def test_elle_esleme_yanlis_sutun(self):
        with self.assertRaises(OkumaHatasi):
            oku(yaz("Ürün;Harcama\nA;1\n"), {"ciro": "Böyle bir sütun yok"})

    def test_sutunlari_goster(self):
        basliklar, esleme = sutunlari_goster(URUN)
        self.assertIn("Harcama (TL)", basliklar)
        self.assertEqual(esleme["harcama"], "Harcama (TL)")
        self.assertIsNone(esleme["terim"])

    def test_xlsx_okunur(self):
        s = Sayfa("Rapor", [20, 10, 10])
        s.satir(1, ["Ürün Adı", "Harcama", "Satış Tutarı"])
        s.satir(2, ["Termos", 120.5, 480])
        yol = Path(tempfile.mkdtemp()) / "r.xlsx"
        yol.write_bytes(kitap_yaz([s]))
        r = oku(yol)
        self.assertEqual((r[0].urun, r[0].harcama, r[0].ciro), ("Termos", 120.5, 480))

    def test_bozuk_ve_desteklenmeyen_dosya(self):
        with self.assertRaises(OkumaHatasi):
            oku(yaz("bu bir excel değil", "r.xlsx"))
        with self.assertRaises(OkumaHatasi):
            oku(yaz("x", "r.xls"))
        with self.assertRaises(OkumaHatasi):
            oku("/yok/boyle/dosya.csv")

    def test_guvenlik_xml_ve_sayilar(self):
        d = Path(tempfile.mkdtemp())
        for ad, govde in (("xxe.xlsx", '<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r>&x;</r>'),
                          ("bomba.xlsx", '<!DOCTYPE r [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;">]><r>&b;</r>')):
            with zipfile.ZipFile(d / ad, "w") as z:
                z.writestr("xl/worksheets/sheet1.xml", '<?xml version="1.0"?>' + govde)
            with self.assertRaises(OkumaHatasi) as h:
                oku(d / ad)
            self.assertIn("güvenlik", str(h.exception))
        self.assertIsNone(sayi("1e308"))
        self.assertIsNone(sayi(float("inf")))
        self.assertEqual(sayi("1.2E+3"), 1200)
        s = oku(yaz("Ürün;Harcama;Satış;Sipariş;Tıklama\nA;-50;-100;-3;-10\n"))
        self.assertEqual((s[0].harcama, s[0].ciro, s[0].siparis, s[0].tiklama), (0, 0, 0, 0))

    def test_maliyet_dosyasi(self):
        m = maliyet_oku(MALIYET)
        self.assertEqual(len(m), 12)
        self.assertEqual((m[0].birim_maliyet, m[0].komisyon, m[0].kargo, m[0].fiyat), (210, 0.20, 45, 459.9))
        m = maliyet_oku(yaz("Ürün;Maliyet;Komisyon\nA;10;0,15\n"))
        self.assertAlmostEqual(m[0].komisyon, 0.15)
        with self.assertRaises(OkumaHatasi):
            maliyet_oku(yaz("Ürün;Maliyet;Komisyon\nA;10;150\n"))


class Analiz(unittest.TestCase):
    def test_toplamlar_ve_oranlar(self):
        r = analiz_et(oku(URUN))
        self.assertAlmostEqual(r.harcama, 14556)
        self.assertAlmostEqual(r.roas, 52177.3 / 14556)
        self.assertAlmostEqual(r.acos, 100 * 14556 / 52177.3)
        self.assertEqual(r.kalemler[0].ad, "Çelik Termos 750 ml")  # harcamaya göre sıralı

    def test_satis_getirmeyen(self):
        r = analiz_et(oku(URUN))
        bos = {k.ad for k in r.kalemler if k.durum == "Satış yok"}
        self.assertEqual(bos, {"Kamp Termosu 1,2 L", "Çay Demlikli Termos", "Sallama Çay Termos Seti"})
        self.assertAlmostEqual(r.satis_getirmeyen_harcama, 1936)

    def test_az_tiklamada_karar_verilmez(self):
        r = analiz_et([ReklamSatiri(urun="A", harcama=30, ciro=0, siparis=0, tiklama=5)])
        self.assertNotEqual(r.kalemler[0].durum, "Satış yok")

    def test_kar_hesabi(self):
        r = analiz_et(oku(URUN), maliyet_oku(MALIYET))
        k = next(k for k in r.kalemler if k.ad == "Çelik Termos 500 ml")
        birim = 389.9 - 190 - 389.9 * 0.20 - 45
        self.assertAlmostEqual(k.birim_kar, birim)
        self.assertAlmostEqual(k.basa_bas_acos, 100 * birim / 389.9)
        self.assertAlmostEqual(k.net, 21 * birim - 2870)
        self.assertEqual(k.durum, "Zarar")
        self.assertLess(r.net, 0)          # panel ROAS 3,6 gösterse de toplamda zarar
        self.assertGreater(r.roas, 3)

    def test_kar_marji(self):
        r = analiz_et([ReklamSatiri(urun="A", harcama=100, ciro=1000, siparis=10, tiklama=200)], kar_marji=25)
        k = r.kalemler[0]
        self.assertAlmostEqual(k.basa_bas_acos, 25)
        self.assertAlmostEqual(k.net, 10 * 25 - 100)
        with self.assertRaises(ValueError):
            analiz_et([ReklamSatiri(urun="A", harcama=1)], kar_marji=120)

    def test_eslesmeyen_maliyet_uyarilir(self):
        r = analiz_et([ReklamSatiri(urun="A", harcama=10, ciro=50, siparis=5), ReklamSatiri(urun="B", harcama=10, ciro=50, siparis=5)],
                      [Maliyet(urun="A", birim_maliyet=2)])
        self.assertEqual(r.eslesmeyen, ["B"])
        self.assertTrue(any("B" in u for u in r.uyarilar))

    def test_reklamsiz_da_zarar(self):
        r = analiz_et([ReklamSatiri(urun="A", harcama=10, ciro=500, siparis=5)], [Maliyet(urun="A", birim_maliyet=120)])
        self.assertEqual(r.kalemler[0].durum, "Reklamsız da zarar")

    def test_oneriler(self):
        turler = [o.tur for o in analiz_et(oku(URUN), maliyet_oku(MALIYET)).oneriler]
        self.assertEqual(turler, ["Bütçe", "Zarar", "Büyüt", "Görsel", "Sayfa"])
        turler = [o.tur for o in analiz_et(oku(URUN)).oneriler]
        self.assertIn("Zarar", turler)     # maliyetsiz: "en pahalı satış"
        terim = analiz_et(oku(TERIM)).oneriler
        self.assertEqual([o.tur for o in terim], ["Terim"] * 3)
        self.assertIn("stanley termos", terim[1].bulgu)

    def test_bos_rapor(self):
        with self.assertRaises(ValueError):
            analiz_et([])


class Cikti(unittest.TestCase):
    def test_komut_satiri(self):
        kod, cikti, _ = main(["analiz", URUN, "--maliyet", MALIYET])
        self.assertEqual(kod, 0)
        self.assertIn("Reklam sonrası kalan", cikti)
        self.assertIn("BULGULAR VE ÖNERİLER (5)", cikti)
        kod, cikti, _ = main(["sutunlar", URUN])
        self.assertIn("harcama        ← Harcama (TL)", cikti)
        kod, _, hata = main(["analiz", URUN, "--sutun", "yanlisbicim"])
        self.assertEqual(kod, 1)
        self.assertIn("alan=", hata)
        kod, _, hata = main(["analiz", URUN, "--sutun", "fiyat=Harcama (TL)"])
        self.assertEqual(kod, 1)
        self.assertIn("bilinmeyen alan", hata)

    def test_excel_gecerli(self):
        r = analiz_et(oku(URUN), maliyet_oku(MALIYET))
        with zipfile.ZipFile(io.BytesIO(dosya(r))) as z:
            for ad in z.namelist():
                if ad.endswith(".xml"):
                    minidom.parseString(z.read(ad))  # bozuk XML olursa hata verir
            self.assertIn("xl/worksheets/sheet3.xml", z.namelist())

    def test_html_kacislanir(self):
        kotu = '<script>alert(1)</script><img src=x onerror=alert(2)>'
        r = analiz_et([ReklamSatiri(urun=kotu, kampanya=kotu, harcama=100, ciro=0, siparis=0, tiklama=50)])
        h = sayfa(r, date(2026, 10, 14), baslik=kotu)
        self.assertNotIn("<script>", h)
        self.assertNotIn("<img", h)
        self.assertIn("&lt;script&gt;", h)

    def test_excel_formul_enjeksiyonu(self):
        r = analiz_et([ReklamSatiri(urun='=HYPERLINK("http://x","tikla")', harcama=10, ciro=20, siparis=1)])
        with zipfile.ZipFile(io.BytesIO(dosya(r))) as z:
            icerik = z.read("xl/worksheets/sheet3.xml").decode()
        self.assertIn("'=HYPERLINK", icerik)
        self.assertNotIn("<f>HYPERLINK", icerik)


SONRAKI = str(KLASOR / "ornek_urun_reklami_sonraki_donem.csv")


class Yonetim(unittest.TestCase):
    def plan(self, yol=URUN, maliyet=MALIYET, gun=None):
        r = analiz_et(oku(yol), maliyet_oku(maliyet) if maliyet else None)
        return r, yonet(r, gun=gun)

    def isler(self, y):
        return {e.hedef: e for e in y.eylemler}

    def test_her_urune_tek_is(self):
        r, y = self.plan()
        self.assertEqual(len(y.eylemler), len(r.kalemler))
        self.assertEqual(len({e.hedef for e in y.eylemler}), len(y.eylemler))

    def test_isler_ve_oranlar(self):
        _, y = self.plan()
        i = self.isler(y)
        self.assertEqual(i["Kamp Termosu 1,2 L"].is_, DURDUR)             # 310 tıklama, satış yok
        self.assertEqual(i["Kamp Termosu 1,2 L"].yeni_harcama, 0)
        self.assertEqual(i["Termos Kupa 350 ml"].is_, DURDUR)             # başa baş için yarıdan fazla düşüş gerekir
        e = i["Çelik Termos 500 ml"]                                      # oran %35,1, başa baş %19,7 → %45
        self.assertEqual((e.is_, e.degisim, e.oncelik), (TEKLIF, -45, 1))
        self.assertAlmostEqual(e.yeni_harcama, 2870 * 0.55)
        self.assertEqual((i["Kahve Termosu 450 ml"].is_, i["Kahve Termosu 450 ml"].degisim), (ARTIR, 20))
        self.assertEqual(i["Çelik Termos 750 ml"].is_, DOKUNMA)           # kârlı ama "büyüt" eşiğinde değil
        self.assertEqual(i["Termos Çanta"].is_, DOKUNMA)                  # az veri
        self.assertEqual([e.oncelik for e in y.eylemler], sorted(e.oncelik for e in y.eylemler))

    def test_butce_toplami(self):
        _, y = self.plan(gun=7)
        self.assertAlmostEqual(y.harcama, sum(e.harcama for e in y.eylemler))
        self.assertAlmostEqual(y.yeni_harcama, y.harcama - y.kesilen + y.eklenen)
        self.assertIn("günde", gunluk(y, y.yeni_harcama))

    def test_maliyetsiz_kar_vaadi_yok(self):
        _, y = self.plan(maliyet=None)
        for e in y.eylemler:
            self.assertNotIn("Kârlı", e.neden)
            if e.is_ == ARTIR:
                self.assertEqual(e.oncelik, 3)
                self.assertIn("kesin değil", e.beklenen)

    def test_arama_terimi_plani(self):
        r, y = self.plan(TERIM, None)
        i = self.isler(y)
        self.assertEqual(i["kamp ocağı"].is_, NEGATIF)
        self.assertEqual(i["çelik termos"].is_, AYIR)
        self.assertEqual(i["stanley termos"].is_, TEKLIF)
        self.assertNotIn("Termoslar - Manuel", i)                         # işler terimlerde, kampanyaya "dokunma" yok
        self.assertAlmostEqual(y.harcama, r.harcama)

    def test_takip(self):
        m = maliyet_oku(MALIYET)
        onceki, simdi = analiz_et(oku(URUN), m), analiz_et(oku(SONRAKI), m)
        y = yonet(simdi, onceki)
        t = {x.hedef: x for x in y.takip}
        self.assertEqual(t["Kamp Termosu 1,2 L"].yapildi, "Yapıldı")
        self.assertEqual(t["Termos Kupa 350 ml"].yapildi, "Yapıldı")       # bu dönemin raporunda yok
        self.assertEqual(t["Sallama Çay Termos Seti"].yapildi, "Yapılmamış görünüyor")
        self.assertEqual(t["Çelik Termos 500 ml"].yapildi, "Yapıldı")
        self.assertIn("Hâlâ zarar", t["Çelik Termos 500 ml"].yorum)
        self.assertEqual(t["Kahve Termosu 450 ml"].yapildi, "Yapıldı")
        self.assertNotIn("Çelik Termos 750 ml", t)                        # "dokunma" işi izlenmez
        self.assertNotIn("Kamp Termosu 1,2 L", self.isler(y))             # harcaması sıfır, yeni işi yok

    def test_takip_artis_bozulursa_geri_al(self):
        m = [Maliyet("A", birim_maliyet=50, fiyat=100)]
        once = analiz_et([ReklamSatiri(urun="A", harcama=100, ciro=1000, siparis=10, tiklama=100)], m)
        simdi = analiz_et([ReklamSatiri(urun="A", harcama=400, ciro=1000, siparis=10, tiklama=300)], m)
        t = yonet(simdi, once).takip[0]
        self.assertEqual((t.yapildi, t.sonuc), ("Yapıldı", "Kötüleşti"))
        self.assertIn("geri alın", t.yorum)

    def test_komut_satiri_ve_ciktilar(self):
        d = Path(tempfile.mkdtemp())
        kod, cikti, _ = main(["analiz", SONRAKI, "--onceki", URUN, "--maliyet", MALIYET, "--gun", "7",
                              "--rapor", str(d / "r.html"), "--excel", str(d / "s.xlsx")])
        self.assertEqual(kod, 0)
        self.assertIn("YAPILACAKLAR", cikti)
        self.assertIn("GEÇEN DÖNEMİN İŞLERİ", cikti)
        h = (d / "r.html").read_text(encoding="utf-8")
        self.assertIn("Yapılacaklar", h)
        self.assertIn("Yapılmamış görünüyor", h)
        with zipfile.ZipFile(d / "s.xlsx") as z:
            kitap = z.read("xl/workbook.xml").decode()
            for ad in z.namelist():
                if ad.endswith(".xml"):
                    minidom.parseString(z.read(ad))
        self.assertIn("Yapılacaklar", kitap)
        self.assertIn("Takip", kitap)
        kod, _, hata = main(["analiz", URUN, "--gun", "0"])
        self.assertEqual(kod, 1)
        self.assertIn("--gun", hata)

    def test_kotu_ad_yeni_bolumlerde(self):
        kotu = '=HYPERLINK("http://x")<script>alert(1)</script>'
        satir = lambda h: [ReklamSatiri(urun=kotu, harcama=h, ciro=0, siparis=0, tiklama=50)]  # noqa: E731
        once, simdi = analiz_et(satir(100)), analiz_et(satir(80))
        y = yonet(simdi, once)
        h = sayfa(simdi, date(2026, 10, 14), "", y)
        self.assertNotIn("<script>", h)
        with zipfile.ZipFile(io.BytesIO(dosya(simdi, y))) as z:
            for ad in ("xl/worksheets/sheet2.xml", "xl/worksheets/sheet3.xml"):
                icerik = z.read(ad).decode()
                self.assertIn("'=HYPERLINK", icerik)
                self.assertNotIn("<f>HYPERLINK", icerik)

if __name__ == "__main__":
    unittest.main()
