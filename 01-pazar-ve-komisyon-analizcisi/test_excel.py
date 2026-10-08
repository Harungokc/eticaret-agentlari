"""Excel çıktısının testleri. Çalıştırmak için: python -m unittest -v"""

import base64
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import arayuz
from agent import main as _main
from excel import komisyon_dosyasi, pazar_dosyasi
from komisyon import analiz_et, veri_yukle
from pazar import Urun
from pazar import analiz_et as pazar_analiz_et

VERI = veri_yukle()
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def main(argv):
    """Aracın komut satırını çalıştırır; ekrana yazdıklarını yutar ki test çıktısı sade kalsın."""
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return _main(argv)



def kat(anahtar):
    return next(k for k in VERI["kategoriler"] if k["anahtar"] == anahtar)


def ac(icerik: bytes) -> dict:
    """xlsx'i açar; {sayfa adı: {hücre: (formül, değer)}} döndürür. Her XML parçası ayrıştırılır."""
    z = zipfile.ZipFile(io.BytesIO(icerik))
    for ad in z.namelist():
        ET.fromstring(z.read(ad))  # bozuk XML burada patlar
    kitap = ET.fromstring(z.read("xl/workbook.xml"))
    sonuc = {}
    for i, s in enumerate(kitap.find("m:sheets", NS), 1):
        hucreler = {}
        for c in ET.fromstring(z.read(f"xl/worksheets/sheet{i}.xml")).iter(f"{{{NS['m']}}}c"):
            f, v, t = c.find("m:f", NS), c.find("m:v", NS), c.find("m:is/m:t", NS)
            deger = t.text if t is not None else (v.text if v is not None else None)
            hucreler[c.get("r")] = (f.text if f is not None else None, deger)
        sonuc[s.get("name")] = hucreler
    return sonuc


def ornek_urunler(n=25):
    return [Urun(ad=f"Ürün {i}", marka=f"Marka {i % 3}", fiyat=100 + i * 20, puan=4.0 + (i % 9) / 10, yorum=50 * (i + 1)) for i in range(n)]


class KomisyonDosyasi(unittest.TestCase):
    def setUp(self):
        self.satirlar = analiz_et(kat("giyim"), 1000, VERI, maliyet=500)
        self.k = ac(komisyon_dosyasi("Giyim", 1000, 500, self.satirlar, VERI))["Komisyon"]

    def test_girdiler_duz_deger_sonuclar_formul(self):
        self.assertEqual(self.k["B4"], (None, "1000"))
        self.assertEqual(self.k["B5"], (None, "500"))
        self.assertIsNone(self.k["B9"][0])  # oran: kullanıcının değiştireceği girdi
        for sutun in "EFGHIJ":
            self.assertIsNotNone(self.k[f"{sutun}9"][0], sutun)  # hesap: formül

    def test_formuller_fiyat_ve_oran_hucrelerine_bagli(self):
        self.assertEqual(self.k["E9"][0], 'IF(OR(B9="",C9=""),"veri yok",$B$4*B9)')
        self.assertEqual(self.k["G9"][0], 'IF(OR(B9="",C9=""),"veri yok",$B$4-F9-$B$4*D9)')
        self.assertEqual(self.k["I9"][0], 'IF(OR(B9="",C9=""),"veri yok",IF($B$5="","",G9-$B$5))')

    def test_onbellekteki_degerler_hesapla_ayni(self):
        for i, s in enumerate(self.satirlar):
            r = 9 + i
            self.assertEqual(self.k[f"A{r}"][1], s.ad)
            self.assertAlmostEqual(float(self.k[f"B{r}"][1]), s.oran_min / 100)
            self.assertAlmostEqual(float(self.k[f"E{r}"][1]), s.komisyon_min)
            self.assertAlmostEqual(float(self.k[f"G{r}"][1]), s.ele_gecen_min)
            self.assertAlmostEqual(float(self.k[f"H{r}"][1]), s.ele_gecen_max)
            self.assertAlmostEqual(float(self.k[f"J{r}"][1]), s.kar_max)

    def test_oran_yoksa_hucre_bos_ve_sonuc_veri_yok(self):
        satirlar = analiz_et(kat("cep_telefonu"), 30000, VERI)
        k = ac(komisyon_dosyasi("Cep telefonu", 30000, None, satirlar, VERI))["Komisyon"]
        r = 9 + next(i for i, s in enumerate(satirlar) if s.pazaryeri == "amazon")
        self.assertEqual(k[f"B{r}"], (None, None))
        self.assertEqual(k[f"G{r}"][1], "veri yok")
        self.assertEqual(k["B5"], (None, None))  # maliyet verilmedi
        dolu = 9 + next(i for i, s in enumerate(satirlar) if s.oran_min is not None)
        self.assertIn(k[f"I{dolu}"][1], (None, ""))  # maliyet yokken kâr boş


class PazarDosyasi(unittest.TestCase):
    def setUp(self):
        self.urunler = ornek_urunler()
        self.rapor = pazar_analiz_et(self.urunler)
        satirlar = analiz_et(kat("kozmetik"), self.rapor.fiyat_medyan, VERI, 100)
        self.kitap = ac(pazar_dosyasi(self.rapor, self.urunler, ("Kozmetik", 100, satirlar), VERI))

    def test_uc_sayfa(self):
        self.assertEqual(list(self.kitap), ["Pazar", "Komisyon", "Ürünler"])
        self.assertEqual(len([h for h in self.kitap["Ürünler"] if h.startswith("C")]), 26)  # başlık + 25 ürün

    def test_ozetler_urun_listesine_formulle_bagli(self):
        p = self.kitap["Pazar"]
        self.assertEqual(p["B5"][0], "COUNT('Ürünler'!$C$2:$C$26)")
        self.assertEqual(p["B8"][0], "MEDIAN('Ürünler'!$C$2:$C$26)")
        self.assertAlmostEqual(float(p["B8"][1]), self.rapor.fiyat_medyan)
        self.assertAlmostEqual(float(p["B7"][1]), self.rapor.fiyat_ceyrek1)
        self.assertEqual(int(float(p["B5"][1])), 25)

    def test_bantlarin_toplami_urun_sayisi(self):
        p = self.kitap["Pazar"]
        toplam = sum(int(float(p[f"C{r}"][1])) for r in range(14, 14 + len(self.rapor.bantlar)))
        self.assertEqual(toplam, 25)
        self.assertIn('"<="&B', p[f"C{13 + len(self.rapor.bantlar)}"][0])  # son bant üst sınırı kapsar
        self.assertIn('"<"&B', p["C14"][0])

    def test_komisyon_fiyati_pazarin_ortancasina_bagli(self):
        self.assertEqual(self.kitap["Komisyon"]["B4"][0], "'Pazar'!B8")

    def test_komisyonsuz_dosya(self):
        self.assertEqual(list(ac(pazar_dosyasi(self.rapor, self.urunler, None, VERI))), ["Pazar", "Ürünler"])


class Guvenlik(unittest.TestCase):
    def test_urun_adi_excelde_formul_olarak_calismaz(self):
        zararli = [Urun(ad='=HYPERLINK("http://kotu.example","tikla")', marka="+cmd|' /C calc'!A0", fiyat=100 + i) for i in range(8)]
        zararli += [Urun(ad="@SUM(1+1)", marka="-2+3", fiyat=500), Urun(ad="normal\x00\x08ad", marka="A&B <c>", fiyat=600)]
        u = ac(pazar_dosyasi(pazar_analiz_et(zararli), zararli, None, VERI))["Ürünler"]
        self.assertEqual(u["A2"], (None, '\'=HYPERLINK("http://kotu.example","tikla")'))
        self.assertTrue(u["B2"][1].startswith("'+"))
        self.assertTrue(u["A10"][1].startswith("'@"))
        self.assertTrue(u["B10"][1].startswith("'-"))
        self.assertEqual(u["A11"][1], "normalad")  # denetim karakterleri atılır
        self.assertEqual(u["B11"][1], "A&B <c>")  # XML özel karakterleri bozulmadan taşınır
        self.assertTrue(all(f is None for f, _ in u.values()))  # Ürünler sayfasında hiç formül yok


class UctanUca(unittest.TestCase):
    def test_komut_satiri_dosyayi_yazar(self):
        with tempfile.TemporaryDirectory() as k:
            hedef = Path(k) / "sonuc"
            self.assertEqual(main(["komisyon", "giyim", "1000", "--excel", str(hedef)]), 0)
            self.assertIn("Komisyon", ac((Path(k) / "sonuc.xlsx").read_bytes()))  # uzantı eklenir
            ornek = str(Path(__file__).parent / "ornek" / "ornek_urunler.csv")
            hedef2 = Path(k) / "pazar.xlsx"
            self.assertEqual(main(["pazar", ornek, "--kategori", "erkek parfüm", "--excel", str(hedef2)]), 0)
            self.assertEqual(list(ac(hedef2.read_bytes())), ["Pazar", "Komisyon", "Ürünler"])

    def test_arayuz_excel_dosyasini_dondurur(self):
        v = arayuz.islem_komisyon({"kategori": "giyim", "fiyat": "1.000", "maliyet": "500"})
        self.assertEqual(v["excel_adi"], "komisyon-karsilastirmasi.xlsx")
        self.assertEqual(ac(base64.b64decode(v["excel"]))["Komisyon"]["B4"], (None, "1000.0"))
        csv = "ad,marka,fiyat,yorum\n" + "\n".join(f"u{i},m,{100 + i},{i}" for i in range(12))
        v = arayuz.islem_pazar({"dosya_adi": "a.csv", "icerik": csv})
        self.assertEqual(list(ac(base64.b64decode(v["excel"]))), ["Pazar", "Ürünler"])
        json.dumps(v)  # yanıt JSON olarak gönderilebilir olmalı


if __name__ == "__main__":
    unittest.main()
