"""Çalıştırmak için: python -m unittest -v"""

import contextlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.dom import minidom

from agent import main as _main
from analiz import Yorum, _yorum_duygusu, analiz_et, konu_listesi, kucult, parcala
from okuyucu import OkumaHatasi, oku
from rapor import dosya

ORNEK = str(Path(__file__).parent / "ornek" / "ornek_yorumlar.csv")


def main(argv):
    cikti, hata = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        kod = _main(argv)
    return kod, cikti.getvalue(), hata.getvalue()


def duygular(metin, puan=None):
    return [p.duygu for p in parcala([Yorum(metin, puan)])]


class Parcalar(unittest.TestCase):
    def test_turkce_kucuk_harf(self):
        self.assertEqual(kucult("İADE ISRARI"), "iade ısrarı")

    def test_ama_cumleyi_ikiye_boler(self):
        p = parcala([Yorum("Ürün çok güzel ama kargo geç geldi", 5)])
        self.assertEqual([(x.duygu, x.konular) for x in p], [("övgü", []), ("şikâyet", ["Kargo ve teslimat"])])

    def test_yuksek_puanli_yorumda_amadan_sonrasi_cekincedir(self):
        self.assertEqual(duygular("Güzel ama kapağı zor açılıyor", 5), ["övgü", "şikâyet"])

    def test_olumsuz_fiil_sikayettir(self):
        for metin in ("Satıcı cevap vermedi", "Tavsiye etmiyorum", "Beğenmedim", "Sünger girmiyor"):
            self.assertEqual(duygular(metin), ["şikâyet"], metin)

    def test_olumsuzlanan_sorun_ovgudur(self):
        for metin in ("Hiç sorun yaşamadım", "Sızdırmıyor", "Koku yapmıyor", "Hiç bozulmadı", "Sorunsuz ulaştı"):
            self.assertEqual(duygular(metin), ["övgü"], metin)

    def test_sorun_ve_olumsuz_fiil_ayri_bolumlerde_karismaz(self):
        self.assertEqual(duygular("Sızdırıyor, kapak tam oturmuyor"), ["şikâyet"])
        self.assertEqual(duygular("Kargoda sorun var, cevap vermediler"), ["şikâyet"])

    def test_dusuk_puanli_yorumda_notr_soz_sikayet_sayilir(self):
        self.assertEqual(duygular("Kumaş beklediğimden farklı", 1), ["şikâyet"])
        self.assertEqual(duygular("Kumaş beklediğimden farklı", None), ["nötr"])

    def test_talep_ovgu_sayilmaz(self):
        p = parcala([Yorum("Keşke kapağı daha sağlam olsaydı", 5)])[0]
        self.assertTrue(p.talep)
        self.assertEqual(p.duygu, "nötr")

    def test_kok_kelimenin_basinda_aranir(self):
        # "paket" kökü "ambalaj paketi"nde bulunur, ama "kargo" kökü "ankargo" gibi bir kelimenin içinde aranmaz.
        self.assertEqual(parcala([Yorum("ankargo diye bir şey")])[0].konular, [])
        self.assertEqual(parcala([Yorum("Paketi sağlamdı")])[0].konular, ["Paketleme", "Kalite ve malzeme"])

    def test_puansiz_yorum_kelimelerden_siniflanir(self):
        self.assertEqual(_yorum_duygusu(Yorum("Berbat, pişman oldum"), "berbat, pişman oldum"), ("olumsuz", False))
        self.assertEqual(_yorum_duygusu(Yorum("Harika, tavsiye ederim"), "harika, tavsiye ederim"), ("olumlu", False))
        self.assertEqual(_yorum_duygusu(Yorum("Berbat", 5), "berbat"), ("olumlu", True))  # puan varsa puan geçerlidir


class Analiz(unittest.TestCase):
    yorumlar = [Yorum("Ürün çok güzel ama kargo geç geldi", 5), Yorum("Kargo geç geldi, paket ezikti", 2),
                Yorum("Kargo hızlı geldi, teşekkürler", 5), Yorum("Keşke kılıfı da olsaydı", 4),
                Yorum("Kapağı sızdırıyor", 1), Yorum("Kapak sızdırıyor, iade ettim", 1), Yorum("İdare eder", 3)]

    def test_sayimlar(self):
        r = analiz_et(self.yorumlar)
        self.assertEqual((r.yorum_sayisi, r.olumlu, r.notr, r.olumsuz), (7, 3, 1, 3))
        self.assertEqual(r.puan_dagilimi, {5: 2, 4: 1, 3: 1, 2: 1, 1: 2})
        self.assertAlmostEqual(r.ortalama_puan, 21 / 7)

    def test_konu_yorum_bazinda_sayilir(self):
        kargo = next(k for k in analiz_et(self.yorumlar).konular if k.ad == "Kargo ve teslimat")
        self.assertEqual((kargo.yorum_sayisi, kargo.sikayet, kargo.ovgu), (3, 2, 1))
        self.assertEqual(kargo.sikayet_ornekleri[0], "kargo geç geldi")

    def test_talepler(self):
        r = analiz_et(self.yorumlar)
        self.assertEqual(r.talepler, [("Keşke kılıfı da olsaydı", [])])
        self.assertEqual(r.talep_iceren_yorum, 1)

    def test_sik_gecen_kelimeler_ekleriyle_gruplanir(self):
        kelimeler = dict(analiz_et(self.yorumlar).olumsuz_kelimeler)
        self.assertEqual(kelimeler.get("sızdırıyor"), 2)
        self.assertEqual(sum(a for k, a in kelimeler.items() if k.startswith("kapa")), 2)  # kapağı + kapak

    def test_ek_konu(self):
        r = analiz_et(self.yorumlar, {"Kapak ve sızdırma": ["kapak", "kapağ", "sızdır"]})
        k = next(k for k in r.konular if k.ad == "Kapak ve sızdırma")
        self.assertEqual((k.ad, k.yorum_sayisi, k.sikayet), ("Kapak ve sızdırma", 2, 2))

    def test_ek_konu_dogrulama(self):
        with self.assertRaises(ValueError):
            konu_listesi({"Boş": []})
        self.assertIn("Kapak sızdırma", konu_listesi({"Kapak*sızdırma": ["kapak"]}))

    def test_az_yorumla_analiz_yapilmaz(self):
        with self.assertRaises(ValueError):
            analiz_et(self.yorumlar[:3])

    def test_yalnizca_yuksek_puan_uyarisi(self):
        r = analiz_et([Yorum(f"Çok güzel {i}", 5) for i in range(6)])
        self.assertTrue(any("düşük puanlı" in u for u in r.uyarilar))

    def test_etiketler_her_yorum_icin(self):
        r = analiz_et(self.yorumlar)
        self.assertEqual(len(r.etiketler), 7)
        self.assertEqual(r.etiketler[0]["sikayet_konulari"], ["Kargo ve teslimat"])
        self.assertTrue(r.etiketler[3]["talep"])


class Okuma(unittest.TestCase):
    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.yol = Path(self.klasor.name)

    def tearDown(self):
        self.klasor.cleanup()

    def yaz(self, metin, ad):
        d = self.yol / ad
        d.write_text(metin, encoding="utf-8")
        return d

    def test_csv(self):
        y = oku(self.yaz('Yorum;Puan\n"Güzel; ama geç geldi";4\nKötü;1,0\nPuansız yorum;\n', "a.csv"))
        self.assertEqual([(x.metin, x.puan) for x in y], [("Güzel; ama geç geldi", 4), ("Kötü", 1), ("Puansız yorum", None)])

    def test_csv_virgullu_ve_yildiz_basligi(self):
        y = oku(self.yaz("yorum,yıldız\nHarika ürün,5\n", "a.csv"))
        self.assertEqual((y[0].metin, y[0].puan), ("Harika ürün", 5))

    def test_txt_satir_satir_ve_puanli(self):
        y = oku(self.yaz("5 | Çok güzel\nKargo geç geldi\n2; Bozuk çıktı\n", "a.txt"))
        self.assertEqual([(x.metin, x.puan) for x in y], [("Çok güzel", 5), ("Kargo geç geldi", None), ("Bozuk çıktı", 2)])

    def test_txt_bos_satirla_ayrilmis(self):
        y = oku(self.yaz("İlk yorum\niki satır\n\nİkinci yorum\n", "a.txt"))
        self.assertEqual(len(y), 2)

    def test_hatalar(self):
        with self.assertRaises(OkumaHatasi):
            oku(self.yaz("puan\n5\n", "a.csv"))
        with self.assertRaises(OkumaHatasi):
            oku(self.yol / "yok.csv")
        with self.assertRaises(OkumaHatasi):
            oku(self.yaz("x", "a.pdf"))
        with self.assertRaises(OkumaHatasi):
            oku(self.yaz("\n\n", "bos.txt"))


class ExcelDosyasi(unittest.TestCase):
    def test_gecerli_dosya(self):
        yorumlar = oku(ORNEK)
        veri = dosya(yorumlar, analiz_et(yorumlar))
        with zipfile.ZipFile(io.BytesIO(veri)) as z:
            self.assertIsNone(z.testzip())
            for ad in z.namelist():
                if ad.endswith((".xml", ".rels")):
                    minidom.parseString(z.read(ad))
            kitap = z.read("xl/workbook.xml").decode("utf-8")
            konular = z.read("xl/worksheets/sheet2.xml").decode("utf-8")
        for ad in ("Özet", "Konular", "Talepler", "Yorumlar"):
            self.assertIn(f'name="{ad}"', kitap)
        self.assertIn("""COUNTIF('Yorumlar'!E2:E41,"*Paketleme*")""", konular)

    def test_yorum_formul_olarak_calismaz(self):
        yorumlar = [Yorum('=HYPERLINK("http://x","tıkla")', 1)] + [Yorum(f"Güzel ürün {i}", 5) for i in range(5)]
        with zipfile.ZipFile(io.BytesIO(dosya(yorumlar, analiz_et(yorumlar)))) as z:
            sayfa = z.read("xl/worksheets/sheet4.xml").decode("utf-8")
        self.assertIn("'=HYPERLINK", sayfa)
        self.assertNotIn("<f>HYPERLINK", sayfa)


class KomutSatiri(unittest.TestCase):
    def test_ornek_veriyle_uctan_uca(self):
        kod, cikti, _ = main(["analiz", ORNEK, "--konu", "Kapak ve sızdırma=kapak,kapağ,sızdır,conta"])
        self.assertEqual(kod, 0)
        for baslik in ("YORUM ANALİZİ — 40 yorum", "Kapak ve sızdırma", "MÜŞTERİ TALEPLERİ", "taşıma askısı"):
            self.assertIn(baslik, cikti)

    def test_excel_ve_konular(self):
        with tempfile.TemporaryDirectory() as k:
            hedef = Path(k) / "sonuc"
            self.assertEqual(main(["analiz", ORNEK, "--excel", str(hedef)])[0], 0)
            self.assertTrue(zipfile.is_zipfile(hedef.with_suffix(".xlsx")))
        kod, cikti, _ = main(["konular"])
        self.assertEqual(kod, 0)
        self.assertIn("Kargo ve teslimat", cikti)

    def test_hata_kodlari(self):
        self.assertEqual(main(["analiz", "yok.csv"])[0], 1)
        kod, _, hata = main(["analiz", ORNEK, "--konu", "yanlış biçim"])
        self.assertEqual(kod, 1)
        self.assertIn("Ek konu anlaşılamadı", hata)


if __name__ == "__main__":
    unittest.main()
