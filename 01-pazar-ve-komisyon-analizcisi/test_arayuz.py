"""Tarayıcı arayüzünün testleri: gerçek bir sunucu açılır ve dışarıdan istek atılır.

Çalıştırmak için: python -m unittest -v
"""

import http.client
import json
import threading
import unittest

import arayuz

CSV = "ad,marka,fiyat,puan,yorum\n" + "\n".join(f"Ürün {i},Marka {i % 3},{100 + i * 20},4.{i % 9},{50 * (i + 1)}" for i in range(25))


class Arayuz(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sunucu = arayuz.sunucu_kur(port=0)
        cls.port = cls.sunucu.server_address[1]
        threading.Thread(target=cls.sunucu.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.sunucu.shutdown()
        cls.sunucu.server_close()

    def istek(self, yontem, yol, govde=None, basliklar=None, ham=None):
        b = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        h = {"Host": f"127.0.0.1:{self.port}"}
        veri = ham
        if govde is not None:
            veri = json.dumps(govde).encode("utf-8")
            h["Content-Type"] = "application/json"
        h.update(basliklar or {})
        b.request(yontem, yol, body=veri, headers=h)
        y = b.getresponse()
        icerik = y.read().decode("utf-8")
        b.close()
        return y, icerik

    def gonder(self, yol, govde, **kw):
        y, icerik = self.istek("POST", yol, govde, **kw)
        return y.status, json.loads(icerik)

    # ---- sayfa

    def test_ana_sayfa(self):
        y, icerik = self.istek("GET", "/")
        self.assertEqual(y.status, 200)
        self.assertIn("Pazar ve Komisyon Analizcisi", icerik)
        self.assertIn('value="ayakkabi"', icerik)
        self.assertIn("frame-ancestors 'none'", y.getheader("Content-Security-Policy"))
        self.assertEqual(y.getheader("X-Content-Type-Options"), "nosniff")

    def test_sunucu_yalnizca_bu_bilgisayari_dinler(self):
        self.assertEqual(self.sunucu.server_address[0], "127.0.0.1")

    def test_bilinmeyen_adres(self):
        self.assertEqual(self.istek("GET", "/../../etc/passwd")[0].status, 404)
        self.assertEqual(self.istek("GET", "/komisyon.py")[0].status, 404)
        self.assertEqual(self.gonder("/api/yok", {})[0], 404)

    # ---- komisyon

    def test_komisyon_hesabi(self):
        kod, v = self.gonder("/api/komisyon", {"kategori": "giyim", "fiyat": "1.000", "maliyet": "500"})
        self.assertEqual(kod, 200)
        self.assertIn("820,00 TL", v["html"])  # Hepsiburada %18
        self.assertIn("Kârınız", v["html"])
        self.assertIn("Amazon Türkiye", v["html"])

    def test_kendi_orani(self):
        _, v = self.gonder("/api/komisyon", {"kategori": "giyim", "fiyat": "1000", "oranlar": {"trendyol": "19", "yok": "5"}})
        self.assertIn("810,00 TL", v["html"])
        self.assertIn("Sizin girdiğiniz oran kullanıldı: Trendyol", v["html"])

    def test_gecersiz_girdiler_anlasilir_hata_verir(self):
        for govde, beklenen in [
            ({"kategori": "giyim", "fiyat": "abc"}, "sayı olmalı"),
            ({"kategori": "giyim", "fiyat": ""}, "boş bırakılamaz"),
            ({"kategori": "giyim", "fiyat": "0"}, "sıfırdan büyük"),
            ({"kategori": "giyim", "fiyat": "-5"}, "eksi olamaz"),
            ({"kategori": "uydurma", "fiyat": "100"}, "kategori seçin"),
            ({"kategori": "giyim", "fiyat": "100", "oranlar": {"trendyol": "2150"}}, "yüzde olarak"),
            ({"kategori": "giyim", "fiyat": "100", "maliyet": "x"}, "sayı olmalı"),
        ]:
            kod, v = self.gonder("/api/komisyon", govde)
            self.assertEqual(kod, 200, govde)
            self.assertIn(beklenen, v["hata"], govde)
            self.assertNotIn("html", v)

    # ---- pazar

    def test_pazar_analizi_ve_komisyon_birlikte(self):
        kod, v = self.gonder("/api/pazar", {"dosya_adi": "liste.csv", "icerik": CSV, "kategori": "kozmetik", "maliyet": "100"})
        self.assertEqual(kod, 200)
        self.assertIn("25 ürün, 3 marka", v["html"])
        self.assertIn("Komisyon karşılaştırması", v["html"])
        self.assertIn("Kozmetik ve kişisel bakım", v["html"])

    def test_dosyadaki_metin_sayfada_calistirilamaz(self):
        zararli = "ad,marka,fiyat,yorum\n" + "\n".join(
            f'x,"<script>alert(1)</script><img src=x onerror=alert(2)>",{100 + i},10' for i in range(10))
        _, v = self.gonder("/api/pazar", {"dosya_adi": "a.csv", "icerik": zararli})
        self.assertNotIn("<script>", v["html"])
        self.assertNotIn("<img", v["html"])
        self.assertIn("&lt;script&gt;", v["html"])

    def test_dosya_adi_diskte_kullanilmaz(self):
        kod, v = self.gonder("/api/pazar", {"dosya_adi": "../../../../tmp/sizinti.csv", "icerik": CSV})
        self.assertEqual(kod, 200)
        self.assertIn("25 ürün", v["html"])
        import os
        self.assertFalse(os.path.exists("/tmp/sizinti.csv"))

    def test_pazar_hatalari(self):
        for govde, beklenen in [
            ({"dosya_adi": "a.exe", "icerik": "x"}, "Desteklenen dosya türleri"),
            ({"dosya_adi": "a.csv", "icerik": ""}, "dosya seçin"),
            ({"dosya_adi": "a.csv", "icerik": "ad,marka\nx,y\n"}, "fiyat"),
            ({"dosya_adi": "a.csv", "icerik": "fiyat\n100\n200\n"}, "en az 8 ürün"),
            ({"dosya_adi": "a.html", "icerik": "<html>boş</html>"}, "ürün listesi bulunamadı"),
            ({"dosya_adi": "a.json", "icerik": "{bozuk"}, ""),
        ]:
            kod, v = self.gonder("/api/pazar", govde)
            self.assertIn(kod, (200, 500), govde)
            self.assertIn("hata", v, govde)
            self.assertIn(beklenen, v["hata"], govde)

    # ---- dışarıdan kötüye kullanım

    def test_baska_siteden_gelen_istek_reddedilir(self):
        govde = {"kategori": "giyim", "fiyat": "100"}
        self.assertEqual(self.gonder("/api/komisyon", govde, basliklar={"Host": "kotu-site.example"})[0], 403)
        self.assertEqual(self.gonder("/api/komisyon", govde, basliklar={"Origin": "https://kotu-site.example"})[0], 403)
        self.assertEqual(self.istek("GET", "/", basliklar={"Host": "kotu-site.example"})[0].status, 403)
        self.assertEqual(self.gonder("/api/komisyon", govde, basliklar={"Origin": f"http://127.0.0.1:{self.port}"})[0], 200)

    def test_form_olarak_gonderilen_istek_reddedilir(self):
        # Başka bir sitedeki düz HTML formu JSON gönderemez; içerik türü kontrolü bunu keser.
        y, _ = self.istek("POST", "/api/komisyon", ham=b'{"kategori":"giyim","fiyat":"1"}',
                          basliklar={"Content-Type": "text/plain"})
        self.assertEqual(y.status, 415)

    def test_cok_buyuk_ve_bozuk_istek(self):
        y, _ = self.istek("POST", "/api/pazar", ham=b"x", basliklar={
            "Content-Type": "application/json", "Content-Length": str(arayuz.EN_BUYUK_ISTEK + 1)})
        self.assertEqual(y.status, 413)
        y, _ = self.istek("POST", "/api/komisyon", ham=b"{bozuk", basliklar={"Content-Type": "application/json"})
        self.assertEqual(y.status, 400)
        y, _ = self.istek("POST", "/api/komisyon", ham=b"[1,2]", basliklar={"Content-Type": "application/json"})
        self.assertEqual(y.status, 400)


if __name__ == "__main__":
    unittest.main()


import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from test_sheets import SahteGoogle

OPENSSL = shutil.which("openssl")
TABLO = "https://docs.google.com/spreadsheets/d/1ku9FJFtbvgYXwa7U5rimba82ra5rJSmka2x9sT3p81Y/edit?gid=0"


@unittest.skipUnless(OPENSSL, "openssl bulunamadı")
class SheetsBaglantisi(unittest.TestCase):
    """Arayüzdeki Google Sheets kurulumu ve gönderimi; Google'a bağlanılmaz."""

    @classmethod
    def setUpClass(cls):
        cls.kok = tempfile.TemporaryDirectory()
        pem = Path(cls.kok.name) / "ozel.pem"
        subprocess.run([OPENSSL, "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(pem)],
                       check=True, capture_output=True)
        cls.anahtar = json.dumps({"type": "service_account", "client_email": "arac@proje.iam.gserviceaccount.com",
                                  "private_key": pem.read_text(), "private_key_id": "kimlik"})

    @classmethod
    def tearDownClass(cls):
        cls.kok.cleanup()

    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.ayar = Path(self.klasor.name) / "ayar"
        os.environ["PAZAR_KOMISYON_AYAR"] = str(self.ayar)
        self.google = SahteGoogle()
        arayuz.SHEETS_HTTP = self.google

    def tearDown(self):
        os.environ.pop("PAZAR_KOMISYON_AYAR", None)
        arayuz.SHEETS_HTTP = None
        self.klasor.cleanup()

    def kur(self):
        return arayuz.islem_sheets_ayar({"tablo": TABLO, "anahtar_icerik": self.anahtar})

    def test_baslangicta_kurulu_degil(self):
        self.assertEqual(arayuz.islem_sheets_durum({}), {"ayarli": False, "hesap": None, "tablo": None, "tablo_adi": None})
        with self.assertRaises(arayuz.GirdiHatasi) as h:
            arayuz.islem_komisyon({"kategori": "giyim", "fiyat": "1000", "sheets": True})
        self.assertIn("kurulmamış", str(h.exception))
        self.assertNotIn("sheets", arayuz.islem_komisyon({"kategori": "giyim", "fiyat": "1000"}))  # istenmeden gönderilmez
        self.assertEqual(self.google.istekler, [])

    def test_kurulum_ve_gonderim(self):
        durum = self.kur()
        self.assertTrue(durum["ayarli"])
        self.assertEqual(durum["hesap"], "arac@proje.iam.gserviceaccount.com")
        self.assertEqual(durum["tablo"], "https://docs.google.com/spreadsheets/d/1ku9FJFtbvgYXwa7U5rimba82ra5rJSmka2x9sT3p81Y/edit")
        dosya = self.ayar / "hizmet-hesabi.json"
        self.assertTrue(dosya.exists())
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(dosya.stat().st_mode), 0o600)
        v = arayuz.islem_komisyon({"kategori": "giyim", "fiyat": "1000", "sheets": True})
        self.assertEqual(v["sheets"]["sekmeler"], ["Komisyon"])
        self.assertEqual(v["sheets"]["hatali_hucre"], 0)
        csv = "ad,marka,fiyat,yorum\n" + "\n".join(f"u{i},m,{100 + i},{i}" for i in range(12))
        v = arayuz.islem_pazar({"dosya_adi": "a.csv", "icerik": csv, "kategori": "kozmetik", "sheets": True})
        self.assertEqual(v["sheets"]["sekmeler"], ["Pazar", "Komisyon", "Ürünler"])

    def test_anahtar_tarayiciya_geri_gonderilmez(self):
        self.kur()
        for yanit in (arayuz.islem_sheets_durum({}), arayuz.islem_komisyon({"kategori": "giyim", "fiyat": "1000", "sheets": True})):
            metin = json.dumps(yanit)
            self.assertNotIn("PRIVATE KEY", metin)
            self.assertNotIn("private_key", metin)

    def test_tablo_adresi_degisince_anahtar_yeniden_istenmez(self):
        self.kur()
        self.assertTrue(arayuz.islem_sheets_ayar({"tablo": "1ku9FJFtbvgYXwa7U5rimba82ra5rJSmka2x9sT3p81Y"})["ayarli"])

    def test_kurulum_hatalari(self):
        for govde, beklenen in [
            ({"tablo": "https://example.com/x", "anahtar_icerik": self.anahtar}, "Tablo adresi anlaşılamadı"),
            ({"tablo": TABLO, "anahtar_icerik": "{bozuk"}, "hizmet hesabı anahtarı değil"),
            ({"tablo": TABLO, "anahtar_icerik": '{"type":"service_account","client_email":"a@b","private_key":"x"}'}, "hizmet hesabı anahtarı değil"),
            ({"tablo": TABLO}, "kurulmamış"),
        ]:
            with self.assertRaises(arayuz.GirdiHatasi) as h:
                arayuz.islem_sheets_ayar(govde)
            self.assertIn(beklenen, str(h.exception), govde.get("tablo"))
        self.assertFalse((self.ayar / "hizmet-hesabi.json").exists())  # geçersiz anahtar diske yazılmaz

    def test_paylasilmamis_tabloda_adres_gosterilir_ve_baglanti_kurulmus_sayilmaz(self):
        arayuz.SHEETS_HTTP = SahteGoogle(api_kodu=403, api_mesaji="The caller does not have permission")
        with self.assertRaises(arayuz.GirdiHatasi) as h:
            self.kur()
        self.assertIn("arac@proje.iam.gserviceaccount.com", str(h.exception))
        durum = arayuz.islem_sheets_durum({})
        self.assertFalse(durum["ayarli"])
        self.assertEqual(durum["hesap"], "arac@proje.iam.gserviceaccount.com")  # paylaşacağı adresi görebilsin

    def test_baglantiyi_kaldir(self):
        self.kur()
        self.assertEqual(arayuz.islem_sheets_kaldir({})["ayarli"], False)
        self.assertEqual(list(self.ayar.iterdir()), [])

    def test_ayarlar_proje_klasorunun_disinda(self):
        os.environ.pop("PAZAR_KOMISYON_AYAR")
        self.assertNotIn(Path(arayuz.__file__).parent.resolve(), arayuz.ayar_klasoru().resolve().parents)
        self.assertEqual(arayuz.ayar_klasoru(), Path.home() / ".pazar-komisyon")
