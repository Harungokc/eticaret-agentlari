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


if __name__ == "__main__":
    unittest.main()
