"""Çalıştırmak için: python -m unittest -v"""

import contextlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from statistics import quantiles
from xml.dom import minidom

from agent import main as _main
from analiz import Urun, ayir, konum, ozet, rakip_karsilastir, yuzdelik
from okuyucu import OkumaHatasi, oku, sayi
from rapor import dosya

ORNEK = str(Path(__file__).parent / "ornek" / "ornek_urunler.csv")


def main(argv):
    """Aracın komut satırını çalıştırır; yazdıklarını döndürür ki test çıktısı sade kalsın."""
    cikti, hata = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        kod = _main(argv)
    return kod, cikti.getvalue(), hata.getvalue()


def liste(fiyatlar, yorumlar=None):
    yorumlar = yorumlar or [None] * len(fiyatlar)
    return [Urun(ad=f"ürün {i}", fiyat=f, yorum=y) for i, (f, y) in enumerate(zip(fiyatlar, yorumlar))]


class Ortalamalar(unittest.TestCase):
    def test_ceyrekler_excel_yontemiyle_ayni(self):
        d = sorted([120.0, 150.0, 199.9, 240.0, 310.0, 480.0, 900.0])
        q1, q2, q3 = quantiles(d, n=4, method="inclusive")
        self.assertAlmostEqual(yuzdelik(d, 0.25), q1)
        self.assertAlmostEqual(yuzdelik(d, 0.5), q2)
        self.assertAlmostEqual(yuzdelik(d, 0.75), q3)

    def test_fiyat_ozeti(self):
        o = ozet(liste([100, 200, 300, 400, 500]))
        self.assertEqual((o.fiyat.en_az, o.fiyat.ortanca, o.fiyat.ortalama, o.fiyat.en_cok), (100, 300, 300, 500))
        self.assertEqual((o.alt_ceyrek, o.ust_ceyrek), (200, 400))

    def test_eksik_veri_uydurulmaz(self):
        o = ozet(liste([100, 200, 300, 400, 500]))
        self.assertEqual((o.puan.adet, o.yorum.adet, o.favori.adet), (0, 0, 0))
        self.assertIsNone(o.puan.ortalama)
        self.assertIsNone(o.yorum_agirlikli_fiyat)
        self.assertIsNone(o.ucretsiz_kargo_orani)

    def test_yorum_agirlikli_fiyat(self):
        o = ozet(liste([100, 200, 300, 400, 500], [0, 0, 0, 0, 10]))
        self.assertEqual(o.yorum_agirlikli_fiyat, 500)

    def test_az_urunle_hesap_yapilmaz(self):
        with self.assertRaises(ValueError):
            ozet(liste([100, 200, 300]))

    def test_aykiri_fiyat_uyarisi(self):
        o = ozet(liste([100, 110, 120, 130, 140, 5000]))
        self.assertTrue(any("ortanca" in u for u in o.uyarilar))


class FiyatKonumu(unittest.TestCase):
    pazar = liste([100, 200, 300, 400, 500, 600, 700, 800], [10, 20, 500, 600, 30, 40, 5, 5])

    def test_sayimlar(self):
        k = konum(self.pazar, 300)
        self.assertEqual((k.daha_ucuz, k.ayni, k.daha_pahali), (2, 1, 5))
        self.assertAlmostEqual(k.yuzdelik, 100 * 2.5 / 8)

    def test_ortanca_ve_ana_aralik(self):
        k = konum(self.pazar, 450)
        self.assertEqual(k.ortanca, 450)
        self.assertEqual(k.ortancadan_fark, 0)
        self.assertEqual(k.ana_aralik, (275, 625))
        self.assertTrue(k.ana_aralikta)
        self.assertFalse(konum(self.pazar, 90).ana_aralikta)

    def test_dilim_etiketleri(self):
        self.assertEqual(konum(self.pazar, 150).dilim, "en ucuz çeyrekte")
        self.assertEqual(konum(self.pazar, 400).dilim, "ortancanın altında")
        self.assertEqual(konum(self.pazar, 500).dilim, "ortancanın üstünde")
        self.assertEqual(konum(self.pazar, 900).dilim, "en pahalı çeyrekte")

    def test_dilimler_her_urunu_bir_kez_sayar(self):
        k = konum(liste([100 + i * 7 for i in range(23)]), 150)
        self.assertEqual(sum(d.urun_sayisi for d in k.dilimler), 23)

    def test_ilgi_goren_dilim(self):
        k = konum(self.pazar, 300)
        self.assertEqual((k.ilgi_goren.alt, k.ilgi_goren.ust), (300, 400))

    def test_az_yorum_verisiyle_ilgi_gosterilmez(self):
        k = konum(liste([100, 200, 300, 400, 500, 600], [1, 2, None, None, None, None]), 300)
        self.assertIsNone(k.ilgi_goren)

    def test_benzer_fiyatli_urunler(self):
        k = konum(self.pazar, 500)  # 450–550 arası
        self.assertEqual(k.yakin_sayisi, 1)

    def test_gecersiz_fiyat(self):
        with self.assertRaises(ValueError):
            konum(self.pazar, 0)


class RakipKarsilastirma(unittest.TestCase):
    def rakipler(self):
        return [Urun("r1", 300, puan=4.0, yorum=100, favori=500, kargo_ucretsiz=True),
                Urun("r2", 400, puan=4.4, yorum=300, favori=900, kargo_ucretsiz=True),
                Urun("r3", 500, puan=4.8, yorum=900, favori=None, kargo_ucretsiz=False)]

    def test_onde_ve_geride(self):
        b = Urun("benim", 350, puan=4.6, yorum=50, favori=1000, kargo_ucretsiz=False, benim=True)
        r = rakip_karsilastir(b, self.rakipler())
        durum = {k.olcu: k.durum for k in r.kiyaslar}
        self.assertEqual(durum, {"Fiyat": "önde", "Puan": "önde", "Yorum sayısı": "geride", "Favori sayısı": "önde", "Kargo": "geride"})
        self.assertEqual(r.geride, ["Yorum sayısı", "Kargo"])

    def test_sira(self):
        b = Urun("benim", 350, puan=4.6, yorum=50, benim=True)
        k = {x.olcu: x for x in rakip_karsilastir(b, self.rakipler()).kiyaslar}
        self.assertEqual((k["Fiyat"].sira, k["Fiyat"].kac_urun), (2, 4))
        self.assertEqual(k["Puan"].sira, 2)
        self.assertEqual(k["Yorum sayısı"].sira, 4)

    def test_bilinmeyen_deger_karsilastirilmaz(self):
        b = Urun("benim", 350, benim=True)
        r = rakip_karsilastir(b, self.rakipler())
        durum = {k.olcu: k.durum for k in r.kiyaslar}
        self.assertEqual(durum["Puan"], "bilinmiyor")
        self.assertEqual(durum["Kargo"], "bilinmiyor")
        self.assertNotIn("Puan", r.onde + r.geride)

    def test_rakipte_olmayan_olcu_tabloya_girmez(self):
        b = Urun("benim", 350, favori=10, benim=True)
        r = rakip_karsilastir(b, [Urun("r1", 300), Urun("r2", 400)])
        self.assertEqual([k.olcu for k in r.kiyaslar], ["Fiyat"])

    def test_kendi_urunu_isaretli_degilse_hata(self):
        with self.assertRaises(ValueError):
            rakip_karsilastir(None, self.rakipler())

    def test_birden_fazla_benim_hata(self):
        with self.assertRaises(ValueError):
            ayir([Urun("a", 1, benim=True), Urun("b", 2, benim=True)])

    def test_kendi_urunu_pazara_karismaz(self):
        benim, pazar = ayir([Urun("a", 100, benim=True)] + liste([200, 300]))
        self.assertEqual((benim.ad, len(pazar)), ("a", 2))


class Okuma(unittest.TestCase):
    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.yol = Path(self.klasor.name)

    def tearDown(self):
        self.klasor.cleanup()

    def yaz(self, metin, ad="a.csv"):
        d = self.yol / ad
        d.write_text(metin, encoding="utf-8")
        return d

    def test_sayi_bicimleri(self):
        self.assertEqual(sayi("1.299,90 TL"), 1299.90)
        self.assertEqual(sayi("1.299"), 1299.0)
        self.assertEqual(sayi("1299.9"), 1299.9)
        self.assertIsNone(sayi("yok"))

    def test_tum_sutunlar(self):
        u = oku(self.yaz("Ürün Adı;Marka;Fiyat;Puan;Yorum Sayısı;Favori;Kargo;Benim\n"
                         "Termos;A;1.299,90;4,5;120;600;ücretsiz;evet\nTermos 2;B;349;;;;35 TL;\n"))
        self.assertEqual((u[0].fiyat, u[0].puan, u[0].yorum, u[0].favori, u[0].kargo_ucretsiz, u[0].benim),
                         (1299.90, 4.5, 120, 600, True, True))
        self.assertEqual((u[1].puan, u[1].yorum, u[1].kargo_ucretsiz, u[1].benim), (None, None, False, False))

    def test_virgullu_dosya_ve_gecersiz_puan(self):
        u = oku(self.yaz("ad,marka,fiyat,puan\nx,y,100,9\n"))
        self.assertEqual((u[0].fiyat, u[0].puan), (100, None))

    def test_fiyatsiz_satir_atilir(self):
        self.assertEqual(len(oku(self.yaz("ad;fiyat\na;100\nb;\nc;0\n"))), 1)

    def test_hatalar(self):
        for metin in ("ad;marka\nx;y\n", "ad;fiyat\nx;yok\n"):
            with self.assertRaises(OkumaHatasi):
                oku(self.yaz(metin))
        with self.assertRaises(OkumaHatasi):
            oku(self.yol / "yok.csv")
        with self.assertRaises(OkumaHatasi):
            oku(self.yaz("x", "a.txt"))


class ExcelDosyasi(unittest.TestCase):
    def kitap(self, urunler):
        benim, pazar = ayir(urunler)
        return dosya(pazar, ozet(pazar), konum(pazar, benim.fiyat), rakip_karsilastir(benim, pazar))

    def test_gecerli_dosya_ve_sayfalar(self):
        veri = self.kitap(oku(ORNEK))
        with zipfile.ZipFile(io.BytesIO(veri)) as z:
            self.assertIsNone(z.testzip())
            for ad in z.namelist():
                if ad.endswith((".xml", ".rels")):
                    minidom.parseString(z.read(ad))
            kitap = z.read("xl/workbook.xml").decode("utf-8")
            konum_sayfasi = z.read("xl/worksheets/sheet2.xml").decode("utf-8")
        for ad in ("Özet", "Konum", "Rakipler", "Ürünler"):
            self.assertIn(f'name="{ad}"', kitap)
        self.assertIn("""<f>COUNTIF('Ürünler'!C2:C31,"&lt;"&amp;B4)</f><v>16</v>""", konum_sayfasi)

    def test_urun_adi_formul_olarak_calismaz(self):
        urunler = [Urun("benim", 300, benim=True)] + [Urun('=HYPERLINK("http://x","y")', 100 + i) for i in range(6)]
        with zipfile.ZipFile(io.BytesIO(self.kitap(urunler))) as z:
            sayfa = z.read("xl/worksheets/sheet4.xml").decode("utf-8")
        self.assertIn("'=HYPERLINK", sayfa)
        self.assertNotIn("<f>HYPERLINK", sayfa)


class KomutSatiri(unittest.TestCase):
    def test_ornek_veriyle_uctan_uca(self):
        kod, cikti, _ = main(["hepsi", ORNEK])
        self.assertEqual(kod, 0)
        for baslik in ("ÜRÜN ORTALAMALARI", "FİYAT KONUMU", "RAKİP KARŞILAŞTIRMASI"):
            self.assertIn(baslik, cikti)

    def test_ayri_komutlar(self):
        self.assertEqual(main(["ortalama", ORNEK])[0], 0)
        kod, cikti, _ = main(["konum", ORNEK, "1.299,90"])
        self.assertEqual(kod, 0)
        self.assertIn("1.299,90 TL", cikti)
        self.assertEqual(main(["rakip", ORNEK])[0], 0)

    def test_excel_yazilir(self):
        with tempfile.TemporaryDirectory() as k:
            hedef = Path(k) / "sonuc"
            self.assertEqual(main(["hepsi", ORNEK, "--excel", str(hedef)])[0], 0)
            self.assertTrue(zipfile.is_zipfile(hedef.with_suffix(".xlsx")))

    def test_hata_kodlari(self):
        self.assertEqual(main(["ortalama", "yok.csv"])[0], 1)
        kod, _, hata = main(["konum", ORNEK, "abc"])
        self.assertEqual(kod, 1)
        self.assertIn("Fiyat anlaşılamadı", hata)

    def test_isaretsiz_listede_rakip_ve_konum(self):
        with tempfile.TemporaryDirectory() as k:
            d = Path(k) / "a.csv"
            d.write_text("ad;fiyat\n" + "\n".join(f"u{i};{100 + i}" for i in range(8)), encoding="utf-8")
            self.assertEqual(main(["rakip", str(d)])[0], 1)
            self.assertEqual(main(["konum", str(d)])[0], 1)
            kod, cikti, _ = main(["hepsi", str(d)])
            self.assertEqual(kod, 0)
            self.assertIn("Rakip karşılaştırması yapılmadı", cikti)


if __name__ == "__main__":
    unittest.main()
