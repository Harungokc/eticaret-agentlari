"""Çalıştırmak için: python -m unittest -v"""

import json
import tempfile
import unittest
from pathlib import Path

from agent import main as _main
from okuyucu import OkumaHatasi, html_oku, oku, sayi
from pazar import Urun, analiz_et


def main(argv):
    """Aracın komut satırını çalıştırır; ekrana yazdıklarını yutar ki test çıktısı sade kalsın."""
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return _main(argv)



def urunler(fiyatlar, yorumlar=None, marka="M"):
    yorumlar = yorumlar or [None] * len(fiyatlar)
    return [Urun(ad=f"ürün {i}", fiyat=f, marka=marka, yorum=y) for i, (f, y) in enumerate(zip(fiyatlar, yorumlar))]


class PazarHesabi(unittest.TestCase):
    def test_fiyat_ozeti(self):
        r = analiz_et(urunler([100, 200, 300, 400, 500, 600, 700, 800, 900]))
        self.assertEqual((r.fiyat_min, r.fiyat_medyan, r.fiyat_max), (100, 500, 900))
        self.assertEqual((r.fiyat_ceyrek1, r.fiyat_ceyrek3), (300, 700))
        self.assertEqual(r.fiyat_ortalama, 500)

    def test_bantlar_her_urunu_bir_kez_sayar(self):
        r = analiz_et(urunler([50, 120, 130, 140, 150, 300, 310, 500, 505, 2000]))
        self.assertEqual(sum(b.urun_sayisi for b in r.bantlar), 10)
        self.assertEqual(r.bantlar[0].alt, 50)
        self.assertEqual(r.bantlar[-1].ust, 2000)

    def test_marka_paylari(self):
        liste = urunler([100] * 6, marka="A") + urunler([200] * 3, marka="B") + urunler([300], marka="C")
        r = analiz_et(liste)
        self.assertEqual(r.marka_sayisi, 3)
        self.assertEqual(r.markalar[0], ("A", 6, 60.0))
        self.assertEqual(r.markalar[1], ("B", 3, 30.0))

    def test_yogunlasmis_pazar(self):
        # 10 ürün yorumların neredeyse tamamını topluyor.
        r = analiz_et(urunler([100 + i for i in range(30)], [10000] * 10 + [10] * 20))
        self.assertGreater(r.ilk10_yorum_payi, 99)
        self.assertEqual(r.yogunluk, "yoğunlaşmış")

    def test_daginik_pazar(self):
        r = analiz_et(urunler([100 + i for i in range(40)], [500] * 40))
        self.assertEqual(r.ilk10_yorum_payi, 25.0)
        self.assertEqual(r.yogunluk, "dağınık")

    def test_az_yorum_verisiyle_yogunluk_hesaplanmaz(self):
        r = analiz_et(urunler([100 + i for i in range(10)], [50] * 10))
        self.assertIsNone(r.yogunluk)
        self.assertTrue(any("20 ürün" in u for u in r.uyarilar))

    def test_yorum_yoksa_uydurulmaz(self):
        r = analiz_et(urunler([100 + i for i in range(10)]))
        self.assertIsNone(r.yorum_medyan)
        self.assertIsNone(r.ilk10_yorum_payi)
        self.assertIsNone(r.bosluk)

    def test_bosluk_az_urunlu_ve_ilgi_goren_bant(self):
        # 100-200 TL kalabalık, 600 TL civarında tek ürün var ve çok yorum almış.
        fiyatlar = [100 + i * 4 for i in range(25)] + [600] + [900 + i * 10 for i in range(10)]
        yorumlar = [100] * 25 + [5000] + [100] * 10
        r = analiz_et(urunler(fiyatlar, yorumlar))
        self.assertIsNotNone(r.bosluk)
        self.assertLessEqual(r.bosluk.alt, 600)
        self.assertGreaterEqual(r.bosluk.ust, 600)

    def test_az_urunle_analiz_yapilmaz(self):
        with self.assertRaises(ValueError):
            analiz_et(urunler([100, 200, 300]))

    def test_fiyatsiz_urun_atilir(self):
        liste = urunler([100 + i for i in range(9)]) + [Urun(ad="bozuk", fiyat=0)]
        self.assertEqual(analiz_et(liste).urun_sayisi, 9)


class Okuma(unittest.TestCase):
    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.yol = Path(self.klasor.name)

    def tearDown(self):
        self.klasor.cleanup()

    def test_sayi_bicimleri(self):
        self.assertEqual(sayi("1.299,90 TL"), 1299.90)
        self.assertEqual(sayi("1299.9"), 1299.9)
        self.assertEqual(sayi("1.299"), 1299.0)
        self.assertEqual(sayi(349), 349.0)
        self.assertIsNone(sayi("yok"))
        self.assertIsNone(sayi(None))

    def test_csv_noktali_virgul_ve_turkce_baslik(self):
        d = self.yol / "a.csv"
        d.write_text("Ürün Adı;Marka;Fiyat;Puan;Yorum Sayısı\nParfüm 1;A;1.299,90;4,5;120\nParfüm 2;B;349;;\n", encoding="utf-8")
        liste = oku(d)
        self.assertEqual(len(liste), 2)
        self.assertEqual((liste[0].fiyat, liste[0].puan, liste[0].yorum, liste[0].marka), (1299.90, 4.5, 120, "A"))
        self.assertIsNone(liste[1].yorum)

    def test_csv_fiyat_sutunu_yoksa_hata(self):
        d = self.yol / "a.csv"
        d.write_text("ad,marka\nx,y\n", encoding="utf-8")
        with self.assertRaises(OkumaHatasi):
            oku(d)

    def test_html_icine_gomulu_urun_listesi(self):
        # Pazaryeri sayfalarındaki gömülü veri biçimine benzeyen yapay bir sayfa.
        durum = {"products": [
            {"name": "Erkek Parfüm \"Fresh\" [50 ml]", "brand": {"name": "A"}, "price": {"sellingPrice": 549.9, "originalPrice": 700},
             "ratingScore": {"averageRating": 4.4, "totalCount": 1250}, "merchantId": 11},
            {"name": "Parfüm 2", "brand": "B", "price": {"discountedPrice": {"value": 320}}, "ratingScore": None},
            {"name": "fiyatsız", "brand": "C"},
        ]}
        d = self.yol / "arama.html"
        d.write_text(f"<html><script>window.__DURUM__ = {json.dumps(durum, ensure_ascii=False)};</script><body></body></html>",
                     encoding="utf-8")
        liste = html_oku(d)
        self.assertEqual(len(liste), 2)
        self.assertEqual((liste[0].fiyat, liste[0].marka, liste[0].puan, liste[0].yorum, liste[0].satici), (549.9, "A", 4.4, 1250, "11"))
        self.assertEqual((liste[1].fiyat, liste[1].marka, liste[1].yorum), (320.0, "B", None))

    def test_html_urun_yoksa_anlasilir_hata(self):
        d = self.yol / "bos.html"
        d.write_text("<html><body>merhaba</body></html>", encoding="utf-8")
        with self.assertRaises(OkumaHatasi):
            oku(d)

    def test_olmayan_dosya_ve_bilinmeyen_tur(self):
        with self.assertRaises(OkumaHatasi):
            oku(self.yol / "yok.csv")
        d = self.yol / "a.txt"
        d.write_text("x", encoding="utf-8")
        with self.assertRaises(OkumaHatasi):
            oku(d)


class KomutSatiri(unittest.TestCase):
    ornek = str(Path(__file__).parent / "ornek" / "ornek_urunler.csv")

    def test_ornek_veriyle_uctan_uca(self):
        self.assertEqual(main(["pazar", self.ornek, "--kategori", "erkek parfüm", "--maliyet", "150"]), 0)

    def test_komisyon_komutu(self):
        self.assertEqual(main(["komisyon", "kadın ayakkabı", "899"]), 0)
        self.assertEqual(main(["komisyon", "uzay mekiği", "100"]), 1)
        self.assertEqual(main(["komisyon", "giyim", "abc"]), 1)

    def test_olmayan_dosya_hata_kodu(self):
        self.assertEqual(main(["pazar", "yok.html"]), 1)


if __name__ == "__main__":
    unittest.main()
