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
