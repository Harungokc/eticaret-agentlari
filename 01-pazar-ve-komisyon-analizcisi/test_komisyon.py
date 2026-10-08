"""Çalıştırmak için: python -m unittest -v"""

import unittest

from agent import sayi_cevir
from komisyon import analiz_et, kategori_bul, kesin_mi, veri_yukle

VERI = veri_yukle()


def kat(anahtar):
    return next(k for k in VERI["kategoriler"] if k["anahtar"] == anahtar)


class KategoriEslestirme(unittest.TestCase):
    def test_tam_ad(self):
        self.assertEqual(kategori_bul("Giyim", VERI).kategori["anahtar"], "giyim")

    def test_es_anlamli_ve_turkce_harf(self):
        self.assertEqual(kategori_bul("KADIN AYAKKABI", VERI).kategori["anahtar"], "ayakkabi")
        self.assertEqual(kategori_bul("sneaker", VERI).kategori["anahtar"], "ayakkabi")

    def test_cumle_icinde_kelime(self):
        self.assertEqual(kategori_bul("siyah deri kadın çanta", VERI).kategori["anahtar"], "canta")

    def test_uzun_es_anlamli_once(self):
        # "telefon kılıfı" cep telefonu oranıyla (%5-7) değil, aksesuar oranıyla (%27) hesaplanmalı.
        self.assertEqual(kategori_bul("iphone telefon kılıfı", VERI).kategori["anahtar"], "telefon_aksesuar")

    def test_bilinmeyen_kategori_uydurulmaz(self):
        e = kategori_bul("uzay mekiği", VERI)
        self.assertIsNone(e.kategori)
        self.assertEqual(e.nasil, "yok")

    def test_bos_metin(self):
        self.assertIsNone(kategori_bul("  ", VERI).kategori)


class Hesap(unittest.TestCase):
    def test_komisyon_ve_ele_gecen(self):
        s = {x.pazaryeri: x for x in analiz_et(kat("giyim"), 1000, VERI)}
        hb = s["hepsiburada"]  # tabloda %18 sabit
        self.assertEqual((hb.komisyon_min, hb.komisyon_max), (180.0, 180.0))
        self.assertEqual((hb.ele_gecen_min, hb.ele_gecen_max), (820.0, 820.0))
        ty = s["trendyol"]  # %17 – %22,5
        self.assertEqual((ty.komisyon_min, ty.komisyon_max), (170.0, 225.0))
        self.assertEqual((ty.ele_gecen_min, ty.ele_gecen_max), (775.0, 830.0))

    def test_n11_ek_kesinti_dusulur(self):
        n11 = next(x for x in analiz_et(kat("giyim"), 1000, VERI) if x.pazaryeri == "n11")
        # %20 – %21 komisyon + %2 hizmet bedeli
        self.assertEqual((n11.ele_gecen_min, n11.ele_gecen_max), (770.0, 780.0))

    def test_kar(self):
        hb = next(x for x in analiz_et(kat("giyim"), 1000, VERI, maliyet=500) if x.pazaryeri == "hepsiburada")
        self.assertEqual((hb.kar_min, hb.kar_max), (320.0, 320.0))

    def test_satici_orani_tabloyu_ezer(self):
        ty = next(x for x in analiz_et(kat("giyim"), 1000, VERI, kendi_oranlari={"trendyol": 19}) if x.pazaryeri == "trendyol")
        self.assertEqual((ty.oran_min, ty.oran_max), (19.0, 19.0))
        self.assertEqual(ty.kaynak, "satıcının girdiği oran")
        self.assertEqual(ty.ele_gecen_min, 810.0)

    def test_veri_yoksa_sayi_uydurulmaz(self):
        amz = next(x for x in analiz_et(kat("cep_telefonu"), 30000, VERI) if x.pazaryeri == "amazon")
        self.assertIsNone(amz.oran_min)
        self.assertIsNone(amz.ele_gecen_min)
        self.assertEqual(amz.kaynak, "veri yok")

    def test_veri_olmayan_pazaryerine_oran_girilebilir(self):
        amz = next(x for x in analiz_et(kat("cep_telefonu"), 30000, VERI, kendi_oranlari={"amazon": 6}) if x.pazaryeri == "amazon")
        self.assertEqual(amz.ele_gecen_min, 28200.0)

    def test_siralama_en_cok_kazandiran_basta_veri_yok_sonda(self):
        satirlar = analiz_et(kat("ayakkabi"), 1000, VERI)
        self.assertEqual(satirlar[-1].kaynak, "veri yok")
        dolu = [s.ele_gecen_orta for s in satirlar if s.ele_gecen_orta is not None]
        self.assertEqual(dolu, sorted(dolu, reverse=True))

    def test_kesinlik(self):
        # Giyimde Amazon %15 ile açık ara önde: aralıklar çakışmıyor.
        self.assertTrue(kesin_mi(analiz_et(kat("giyim"), 1000, VERI)))
        # Trendyol %18 girilirse Hepsiburada (%18) ile eşit; kesin değil.
        self.assertFalse(kesin_mi(analiz_et(kat("oyuncak"), 1000, VERI, kendi_oranlari={"trendyol": 18})))

    def test_gecersiz_fiyat(self):
        with self.assertRaises(ValueError):
            analiz_et(kat("giyim"), 0, VERI)


class SayiOkuma(unittest.TestCase):
    def test_bicimler(self):
        self.assertEqual(sayi_cevir("899"), 899.0)
        self.assertEqual(sayi_cevir("1.299,90"), 1299.90)
        self.assertEqual(sayi_cevir("1299.90"), 1299.90)
        self.assertEqual(sayi_cevir("249 TL"), 249.0)


class VeriButunlugu(unittest.TestCase):
    def test_her_oran_gecerli_ve_kaynakli(self):
        for k in VERI["kategoriler"]:
            for pz, o in k["oranlar"].items():
                self.assertIn(pz, VERI["pazaryerleri"], k["anahtar"])
                if o is None:
                    continue
                self.assertLessEqual(0, o["min"])
                self.assertLessEqual(o["min"], o["max"])
                self.assertLess(o["max"], 50)
                self.assertTrue(o["kaynak"], f"{k['anahtar']}/{pz} kaynaksız")
                for kay in o["kaynak"]:
                    self.assertIn(kay, VERI["kaynaklar"])


if __name__ == "__main__":
    unittest.main()
