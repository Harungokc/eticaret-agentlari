"""Çalıştırmak için: python -m unittest -v"""

import contextlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.dom import minidom

from agent import main as _main
from analiz import BOLGELER, IL_BOLGESI, Siparis, analiz_et, baslik, il_bul
from okuyucu import OkumaHatasi, oku
from rapor import dosya

ORNEK = str(Path(__file__).parent / "ornek" / "ornek_siparisler.csv")


def main(argv):
    cikti, hata = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        kod = _main(argv)
    return kod, cikti.getvalue(), hata.getvalue()


def sip(il, **kw):
    return Siparis(il=il_bul(il), il_ham=il, **kw)


class Iller(unittest.TestCase):
    def test_81_il_ve_7_bolge(self):
        self.assertEqual(len(IL_BOLGESI), 81)
        self.assertEqual(len(BOLGELER), 7)
        self.assertEqual(sum(len(i) for i in BOLGELER.values()), 81)  # hiçbir il iki bölgede değil

    def test_yazim_farklari(self):
        for yazim in ("İSTANBUL", "istanbul", "Istanbul ", " İstanbul"):
            self.assertEqual(il_bul(yazim), "İstanbul", yazim)
        self.assertEqual(il_bul("IGDIR"), "Iğdır")
        self.assertEqual(il_bul("ÇANAKKALE"), "Çanakkale")
        self.assertEqual(il_bul("Hakkâri"), "Hakkari")

    def test_eski_ve_kisa_adlar(self):
        self.assertEqual([il_bul(x) for x in ("Urfa", "K.Maraş", "Afyon", "İçel", "Antep", "İzmit")],
                         ["Şanlıurfa", "Kahramanmaraş", "Afyonkarahisar", "Mersin", "Gaziantep", "Kocaeli"])

    def test_taninmayan(self):
        for yazim in ("", None, "Almanya", "Kadıköy"):
            self.assertIsNone(il_bul(yazim))

    def test_ilce_yazimi(self):
        self.assertEqual((baslik("KADIKÖY"), baslik("izmit"), baslik("  ıSPARTA  merkez")), ("Kadıköy", "İzmit", "Isparta Merkez"))


class Analiz(unittest.TestCase):
    def liste(self):
        return ([sip("İstanbul", ilce="KADIKÖY", tutar=100.0, urun="A")] * 6 + [sip("istanbul", ilce="Kadıköy", tutar=200.0, urun="B")] * 2
                + [sip("Ankara", ilce="Çankaya", tutar=300.0, urun="B", iade=True)] + [sip("Ankara", tutar=300.0, urun="B")]
                + [sip("Almanya", tutar=50.0)] + [sip("İzmir", tutar=999.0, iptal=True)])

    def test_il_sayimlari(self):
        r = analiz_et(self.liste())
        self.assertEqual((r.siparis_sayisi, r.il_sayisi, r.ciro), (10, 2, 1600.0))
        ist, ank = r.iller
        self.assertEqual((ist.ad, ist.siparis, ist.pay, ist.ciro, ist.ortalama_sepet, ist.bolge), ("İstanbul", 8, 80.0, 1000.0, 125.0, "Marmara"))
        self.assertEqual((ank.siparis, ank.iade, ank.iade_orani, ank.ciro_payi), (2, 1, 50.0, 37.5))

    def test_iptal_ve_taninmayan_disarida(self):
        r = analiz_et(self.liste())
        self.assertEqual((r.iptal, r.taninmayan, r.taninmayan_ornekleri), (1, 1, ["Almanya"]))
        self.assertNotIn("İzmir", [x.ad for x in r.iller])
        self.assertIn("İzmir", r.siparis_gelmeyen_iller)
        self.assertEqual(len(r.siparis_gelmeyen_iller), 79)

    def test_bolge_ve_ilce(self):
        r = analiz_et(self.liste())
        self.assertEqual([(b.ad, b.siparis) for b in r.bolgeler], [("Marmara", 8), ("İç Anadolu", 2)])
        self.assertEqual([(i.ad, i.siparis) for i in r.ilceler], [("İstanbul / Kadıköy", 8), ("Ankara / Çankaya", 1)])

    def test_en_cok_satan_ve_yogunlasma(self):
        r = analiz_et(self.liste())
        self.assertEqual([x.en_cok_satan for x in r.iller], ["A", "B"])
        self.assertEqual((r.ilk3_pay, r.ilk10_pay), (100.0, 100.0))

    def test_ayni_siparis_numarasi_bir_kez_sayilir(self):
        satirlar = [sip("Bursa", no="1", tutar=50.0), sip("Bursa", no="1", tutar=70.0)] + [sip("Bursa", no=str(i), tutar=10.0) for i in range(2, 11)]
        r = analiz_et(satirlar)
        self.assertEqual((r.siparis_sayisi, r.ciro, r.iller[0].ortalama_sepet), (10, 210.0, 21.0))

    def test_tutar_yoksa_ciro_hesaplanmaz(self):
        r = analiz_et([sip("Bursa")] * 12)
        self.assertIsNone(r.ciro)
        self.assertIsNone(r.iller[0].ortalama_sepet)
        self.assertIsNone(r.iller[0].iade_orani)  # iade bilgisi de yok

    def test_az_siparisle_analiz_yapilmaz(self):
        with self.assertRaises(ValueError):
            analiz_et([sip("Bursa")] * 4 + [sip("Almanya")] * 20)


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

    def test_pazaryeri_basliklari_ve_durum(self):
        s = oku(self.yaz("Sipariş Numarası;Alıcı;Telefon;Teslimat Adresi;İl;İlçe;Ürün Adı;Faturalanacak Tutar;Sipariş Statüsü\n"
                         "77;Ad Soyad;0500;Bir sokak no 1;İSTANBUL;KADIKÖY;Termos;1.299,90;Teslim Edildi\n"
                         "78;Ad Soyad;0500;Bir sokak no 2;ankara;;Kupa;279,9;İADE EDİLDİ\n"
                         "79;Ad Soyad;0500;Bir sokak;İzmir;;Kupa;10;İptal Edildi\n"))
        self.assertEqual([(x.il, x.ilce, x.tutar, x.urun, x.no, x.iade, x.iptal) for x in s],
                         [("İstanbul", "KADIKÖY", 1299.90, "Termos", "77", False, False), ("Ankara", "", 279.9, "Kupa", "78", True, False),
                          ("İzmir", "", 10.0, "Kupa", "79", False, True)])

    def test_kisisel_sutunlar_okunmaz(self):
        s = oku(self.yaz("il,alıcı,telefon,adres\nBursa,Gizli Kişi,05001112233,Gizli Sokak 5\n"))[0]
        self.assertNotIn("Gizli", repr(s))
        self.assertNotIn("0500", repr(s))

    def test_hatalar(self):
        with self.assertRaises(OkumaHatasi):
            oku(self.yaz("ilçe;tutar\nKadıköy;10\n"))
        with self.assertRaises(OkumaHatasi):
            oku(self.yol / "yok.csv")
        with self.assertRaises(OkumaHatasi):
            oku(self.yaz("x", "a.xlsx"))


class ExcelVeKomut(unittest.TestCase):
    def test_gecerli_dosya_ve_kisisel_veri_yok(self):
        d = Path(tempfile.mkdtemp()) / "a.csv"
        d.write_text("il;alıcı;tutar\n" + "\n".join(f"Bursa;Gizli Kişi {i};10" for i in range(12)), encoding="utf-8")
        siparisler = oku(d)
        veri = dosya(siparisler, analiz_et(siparisler))
        with zipfile.ZipFile(io.BytesIO(veri)) as z:
            self.assertIsNone(z.testzip())
            icerik = ""
            for ad in z.namelist():
                if ad.endswith((".xml", ".rels")):
                    minidom.parseString(z.read(ad))
                    icerik += z.read(ad).decode("utf-8")
        for ad in ("Özet", "İller", "İlçeler", "Siparişler"):
            self.assertIn(f'name="{ad}"', icerik)
        self.assertNotIn("Gizli", icerik)

    def test_ornek_veriyle_uctan_uca(self):
        kod, cikti, _ = main(["analiz", ORNEK])
        self.assertEqual(kod, 0)
        for metin in ("SATIŞ BÖLGE ANALİZİ", "Marmara", "İstanbul", "SİPARİŞ GELMEYEN İLLER"):
            self.assertIn(metin, cikti)

    def test_excel_ve_hata_kodu(self):
        with tempfile.TemporaryDirectory() as k:
            hedef = Path(k) / "sonuc"
            self.assertEqual(main(["analiz", ORNEK, "--excel", str(hedef)])[0], 0)
            self.assertTrue(zipfile.is_zipfile(hedef.with_suffix(".xlsx")))
        self.assertEqual(main(["analiz", "yok.csv"])[0], 1)


if __name__ == "__main__":
    unittest.main()
