"""Google Sheets çıktısının testleri. Google'a bağlanılmaz: ağ katmanı sahte bir işlevle değiştirilir.

İmza testleri için sistemde `openssl` gerekir; yoksa o testler atlanır.
Çalıştırmak için: python -m unittest -v
"""

import base64
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, unquote

from agent import main as _main
from excel import komisyon_sayfalari, pazar_sayfalari
from komisyon import analiz_et, veri_yukle
from pazar import Urun
from pazar import analiz_et as pazar_analiz_et
from sheets import (Istemci, SheetsHatasi, anahtar_oku, formul_cevir, jwt_olustur, rs256_imzala, rsa_anahtari_coz,
                    sayfa_istekleri, tablo_kimligi)

VERI = veri_yukle()
OPENSSL = shutil.which("openssl")
KIMLIK = "1ku9FJFtbvgYXwa7U5rimba82ra5rJSmka2x9sT3p81Y"


def main(argv):
    """Aracın komut satırını çalıştırır; ekrana yazdıklarını yutar ki test çıktısı sade kalsın."""
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return _main(argv)



def kat(anahtar):
    return next(k for k in VERI["kategoriler"] if k["anahtar"] == anahtar)


def komisyon_ornegi():
    return komisyon_sayfalari("Giyim", 1000, 500, analiz_et(kat("giyim"), 1000, VERI, maliyet=500), VERI)


class SahteGoogle:
    """Sheets API'nin bu aracın kullandığı kısmını taklit eder ve gelen istekleri kaydeder."""

    def __init__(self, sekmeler=("Sayfa1",), dil="tr_TR", hatali=(0,), jeton_kodu=200, api_kodu=200, api_mesaji=""):
        self.sekmeler = {ad: i * 100 for i, ad in enumerate(sekmeler)}
        self.dil, self.hatali, self.jeton_kodu, self.api_kodu, self.api_mesaji = dil, list(hatali), jeton_kodu, api_kodu, api_mesaji
        self.istekler, self.jeton_istegi = [], None

    def __call__(self, yontem, adres, govde, basliklar):
        if "oauth2" in adres or adres.endswith("/token"):
            self.jeton_istegi = (adres, govde, basliklar)
            if self.jeton_kodu != 200:
                return self.jeton_kodu, b'{"error":"invalid_grant","error_description":"Invalid JWT Signature."}'
            return 200, b'{"access_token":"sahte-jeton","expires_in":3600}'
        self.istekler.append((yontem, adres, json.loads(govde) if govde else None, basliklar))
        if self.api_kodu != 200:
            return self.api_kodu, json.dumps({"error": {"message": self.api_mesaji}}).encode()
        if yontem == "GET" and "effectiveValue" in adres:
            n = self.hatali.pop(0) if self.hatali else 0
            return 200, json.dumps({"sheets": [{"data": [{"rowData": [{"values": [{"effectiveValue": {"errorValue": {"type": "ERROR", "message": "Formula parse error."}}}] * n}]}]}]}).encode()
        if yontem == "GET":
            return 200, json.dumps({"properties": {"locale": self.dil}, "sheets": [
                {"properties": {"sheetId": no, "title": ad}} for ad, no in self.sekmeler.items()]}).encode()
        yanitlar = []
        for i in json.loads(govde)["requests"]:
            if "addSheet" in i:
                ad = i["addSheet"]["properties"]["title"]
                self.sekmeler[ad] = 1000 + len(self.sekmeler)
                yanitlar.append({"addSheet": {"properties": {"title": ad, "sheetId": self.sekmeler[ad]}}})
        return 200, json.dumps({"replies": yanitlar}).encode()

    def toplu(self):
        return [g["requests"] for y, a, g, _ in self.istekler if y == "POST"]


@unittest.skipUnless(OPENSSL, "openssl bulunamadı")
class Imza(unittest.TestCase):
    """Elle yazılan RS256 imzası, OpenSSL ile doğrulanır."""

    @classmethod
    def setUpClass(cls):
        cls.klasor = tempfile.TemporaryDirectory()
        k = Path(cls.klasor.name)
        subprocess.run([OPENSSL, "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(k / "ozel.pem")],
                       check=True, capture_output=True)
        subprocess.run([OPENSSL, "pkey", "-in", str(k / "ozel.pem"), "-pubout", "-out", str(k / "acik.pem")], check=True, capture_output=True)
        subprocess.run([OPENSSL, "pkey", "-in", str(k / "ozel.pem"), "-traditional", "-out", str(k / "pkcs1.pem")], check=True, capture_output=True)
        cls.k, cls.pem = k, (k / "ozel.pem").read_text()
        cls.anahtar = {"type": "service_account", "client_email": "arac@proje.iam.gserviceaccount.com", "private_key": cls.pem,
                       "token_uri": "https://oauth2.googleapis.com/token"}

    @classmethod
    def tearDownClass(cls):
        cls.klasor.cleanup()

    def dogrula(self, mesaj: bytes, imza: bytes) -> bool:
        (self.k / "mesaj").write_bytes(mesaj)
        (self.k / "imza").write_bytes(imza)
        s = subprocess.run([OPENSSL, "dgst", "-sha256", "-verify", str(self.k / "acik.pem"), "-signature", str(self.k / "imza"),
                            str(self.k / "mesaj")], capture_output=True)
        return s.returncode == 0

    def test_imza_openssl_ile_dogrulanir(self):
        n, d = rsa_anahtari_coz(self.pem)
        for mesaj in (b"merhaba", b"", "Türkçe karakterli içerik: şğıöçü".encode(), b"x" * 5000):
            self.assertTrue(self.dogrula(mesaj, rs256_imzala(mesaj, n, d)), mesaj[:20])

    def test_degisen_mesaj_dogrulanmaz(self):
        n, d = rsa_anahtari_coz(self.pem)
        self.assertFalse(self.dogrula(b"baska mesaj", rs256_imzala(b"merhaba", n, d)))

    def test_pkcs1_bicimindeki_anahtar_da_cozulur(self):
        self.assertEqual(rsa_anahtari_coz((self.k / "pkcs1.pem").read_text()), rsa_anahtari_coz(self.pem))

    def test_jwt_icerigi_ve_imzasi(self):
        jwt = jwt_olustur(self.anahtar, simdi=1_800_000_000)
        baslik, govde, imza = jwt.split(".")
        coz = lambda p: base64.urlsafe_b64decode(p + "=" * (-len(p) % 4))
        self.assertEqual(json.loads(coz(baslik)), {"alg": "RS256", "typ": "JWT"})
        g = json.loads(coz(govde))
        self.assertEqual(g["iss"], "arac@proje.iam.gserviceaccount.com")
        self.assertEqual(g["scope"], "https://www.googleapis.com/auth/spreadsheets")  # yalnızca tablolar; Drive'ın tamamı değil
        self.assertEqual(g["aud"], "https://oauth2.googleapis.com/token")
        self.assertEqual(g["exp"] - g["iat"], 3600)
        self.assertTrue(self.dogrula(f"{baslik}.{govde}".encode(), coz(imza)))

    def test_uctan_uca_yazma(self):
        google = SahteGoogle()
        sonuc = Istemci(self.anahtar, google).yaz(f"https://docs.google.com/spreadsheets/d/{KIMLIK}/edit#gid=0", komisyon_ornegi())
        adres, govde, _ = google.jeton_istegi
        self.assertEqual(adres, "https://oauth2.googleapis.com/token")
        alanlar = parse_qs(govde.decode())
        self.assertEqual(alanlar["grant_type"], ["urn:ietf:params:oauth:grant-type:jwt-bearer"])
        self.assertEqual(alanlar["assertion"][0].count("."), 2)
        self.assertTrue(all(b["Authorization"] == "Bearer sahte-jeton" for *_, b in google.istekler))
        self.assertTrue(all(a.startswith(f"https://sheets.googleapis.com/v4/spreadsheets/{KIMLIK}") for _, a, _, _ in google.istekler))
        self.assertEqual(sonuc["eklenen_sekmeler"], ["Komisyon"])
        self.assertEqual(sonuc["hatali_hucre"], 0)
        self.assertIn(KIMLIK, sonuc["adres"])

    def test_anahtar_dosyasindan_komut_satirina(self):
        yol = self.k / "hizmet-hesabi.json"
        yol.write_text(json.dumps(self.anahtar))
        self.assertEqual(anahtar_oku(yol)["client_email"], self.anahtar["client_email"])
        # Anahtarsız --sheets anlaşılır hata verir, ağa çıkılmaz.
        self.assertEqual(main(["komisyon", "giyim", "1000", "--sheets", KIMLIK]), 1)


class Yardimcilar(unittest.TestCase):
    def test_tablo_kimligi(self):
        self.assertEqual(tablo_kimligi(f"https://docs.google.com/spreadsheets/d/{KIMLIK}/edit?pli=1&gid=0#gid=0"), KIMLIK)
        self.assertEqual(tablo_kimligi(f"  {KIMLIK}  "), KIMLIK)
        for bozuk in ("", "https://example.com/tablo", "kisa", "https://docs.google.com/document/d/abc"):
            with self.assertRaises(SheetsHatasi):
                tablo_kimligi(bozuk)

    def test_formul_ayiricisi_tirnak_icine_dokunmaz(self):
        self.assertEqual(formul_cevir('IF(OR(B9="",C9=""),"veri yok",$B$4*B9)', ";"), 'IF(OR(B9="";C9="");"veri yok";$B$4*B9)')
        self.assertEqual(formul_cevir('IF(A1="a,b",1,2)', ";"), 'IF(A1="a,b";1;2)')
        self.assertEqual(formul_cevir("COUNTIF('Ür,ünler'!$B$2:$B$9,A1)", ";"), "COUNTIF('Ür,ünler'!$B$2:$B$9;A1)")
        self.assertEqual(formul_cevir("SUM(1,2)", ","), "SUM(1,2)")

    def test_anahtar_dosyasi_hatalari(self):
        with tempfile.TemporaryDirectory() as k:
            with self.assertRaises(SheetsHatasi):
                anahtar_oku(Path(k) / "yok.json")
            for icerik in ("{bozuk", "[]", '{"type":"authorized_user"}', '{"type":"service_account","client_email":"a@b"}'):
                d = Path(k) / "a.json"
                d.write_text(icerik)
                with self.assertRaises(SheetsHatasi):
                    anahtar_oku(d)
        for pem in ("", "-----BEGIN PRIVATE KEY-----\nAAAA\n-----END PRIVATE KEY-----", "çöp"):
            with self.assertRaises(SheetsHatasi):
                rsa_anahtari_coz(pem)


class Istekler(unittest.TestCase):
    def test_hucreler_formul_ve_girdi_olarak_yazilir(self):
        istekler = sayfa_istekleri(komisyon_ornegi()[0], 7, ";")
        self.assertEqual(list(istekler[0]), ["unmergeCells"])
        self.assertNotIn("rows", istekler[1]["updateCells"])  # önce temizlik
        satirlar = istekler[2]["updateCells"]["rows"]
        self.assertEqual(istekler[2]["updateCells"]["start"], {"sheetId": 7, "rowIndex": 0, "columnIndex": 0})
        hucre = lambda a1_satir, sutun: satirlar[a1_satir - 1]["values"][sutun - 1]
        self.assertEqual(hucre(4, 2)["userEnteredValue"], {"numberValue": 1000})  # B4 fiyat: girdi
        self.assertEqual(hucre(4, 2)["userEnteredFormat"]["backgroundColor"], {"red": 1.0, "green": 1.0, "blue": 0.0})
        self.assertEqual(hucre(9, 5)["userEnteredValue"], {"formulaValue": '=IF(OR(B9="";C9="");"veri yok";$B$4*B9)'})
        self.assertEqual(hucre(9, 2)["userEnteredFormat"]["numberFormat"]["type"], "PERCENT")
        self.assertIn({"mergeCells": {"range": {"sheetId": 7, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0,
                                                "endColumnIndex": 11}, "mergeType": "MERGE_ALL"}}, istekler)
        self.assertEqual(istekler[-1]["updateSheetProperties"]["properties"]["gridProperties"]["frozenRowCount"], 8)

    def test_urun_adi_formul_olarak_yazilmaz(self):
        urunler = [Urun(ad='=IMPORTDATA("http://kotu.example")', marka="+1", fiyat=100 + i) for i in range(8)]
        sayfalar = pazar_sayfalari(pazar_analiz_et(urunler), urunler, None, VERI)
        urun_sayfasi = next(s for s in sayfalar if s.ad == "Ürünler")
        satirlar = sayfa_istekleri(urun_sayfasi, 1, ",")[2]["updateCells"]["rows"]
        self.assertEqual(satirlar[1]["values"][0]["userEnteredValue"], {"stringValue": '=IMPORTDATA("http://kotu.example")'})
        self.assertFalse(any("formulaValue" in h.get("userEnteredValue", {}) for r in satirlar for h in r["values"]))


class Akis(unittest.TestCase):
    anahtar = {"type": "service_account", "client_email": "arac@proje.iam.gserviceaccount.com", "private_key": "x"}

    def istemci(self, google):
        i = Istemci(self.anahtar, google)
        i._jeton, i._bitis = "sahte-jeton", 9e12  # jeton alma adımı imza testlerinde sınanıyor
        return i

    def test_var_olan_sekme_yeniden_kullanilir_digerlerine_dokunulmaz(self):
        google = SahteGoogle(sekmeler=("Sayfa1", "Komisyon"))
        sonuc = self.istemci(google).yaz(KIMLIK, komisyon_ornegi())
        self.assertEqual(sonuc["eklenen_sekmeler"], [])
        istekler = [i for t in google.toplu() for i in t]
        self.assertFalse(any("addSheet" in i or "deleteSheet" in i for i in istekler))
        dokunulan = {json.dumps(i).count('"sheetId": 0') for i in istekler}
        self.assertEqual(dokunulan, {0})  # Sayfa1 (sheetId 0) hiçbir istekte geçmez
        self.assertTrue(sonuc["adres"].endswith("#gid=100"))

    def test_eksik_sekmeler_eklenir(self):
        urunler = [Urun(ad=f"u{i}", marka="m", fiyat=100 + i, yorum=i) for i in range(12)]
        rapor = pazar_analiz_et(urunler)
        satirlar = analiz_et(kat("kozmetik"), rapor.fiyat_medyan, VERI)
        google = SahteGoogle()
        sonuc = self.istemci(google).yaz(KIMLIK, pazar_sayfalari(rapor, urunler, ("Kozmetik", None, satirlar), VERI))
        self.assertEqual(sonuc["eklenen_sekmeler"], ["Pazar", "Komisyon", "Ürünler"])
        self.assertEqual([i["addSheet"]["properties"]["title"] for i in google.toplu()[0]], ["Pazar", "Komisyon", "Ürünler"])

    def test_yazilan_sekmeler_basa_alinir(self):
        urunler = [Urun(ad=f"u{i}", marka="m", fiyat=100 + i, yorum=i) for i in range(12)]
        google = SahteGoogle(sekmeler=("Sayfa1", "Notlarım"))
        self.istemci(google).yaz(KIMLIK, pazar_sayfalari(pazar_analiz_et(urunler), urunler, None, VERI))
        siralama = [(i["updateSheetProperties"]["properties"]["sheetId"], i["updateSheetProperties"]["properties"]["index"])
                    for i in google.toplu()[-1] if i.get("updateSheetProperties", {}).get("fields") == "index"]
        self.assertEqual(siralama, [(google.sekmeler["Pazar"], 0), (google.sekmeler["Ürünler"], 1)])
        self.assertFalse(any("deleteSheet" in i for t in google.toplu() for i in t))

    def test_dile_gore_ayirici(self):
        for dil, beklenen in (("tr_TR", ";"), ("en_US", ","), ("de_DE", ";")):
            google = SahteGoogle(dil=dil)
            self.istemci(google).yaz(KIMLIK, komisyon_ornegi())
            self.assertIn(f'=IF(OR(B9=""{beklenen}C9="")', json.dumps(google.toplu()[-1], ensure_ascii=False).replace('\\"', '"'), dil)

    def test_hata_cikarsa_diger_ayirici_denenir(self):
        google = SahteGoogle(dil="tr_TR", hatali=(24, 0))
        sonuc = self.istemci(google).yaz(KIMLIK, komisyon_ornegi())
        self.assertEqual(sonuc["hatali_hucre"], 0)
        self.assertIn('OR(B9=\\"\\",C9', json.dumps(google.toplu()[-1]))  # ikinci denemede virgül kullanıldı

    def test_iki_ayirici_da_hata_verirse_bildirilir(self):
        google = SahteGoogle(dil="tr_TR", hatali=(3, 5, 3))
        self.assertEqual(self.istemci(google).yaz(KIMLIK, komisyon_ornegi())["hatali_hucre"], 3)

    def test_paylasilmamis_tablo_icin_ne_yapilacagi_soylenir(self):
        for kod in (403, 404):
            with self.assertRaises(SheetsHatasi) as h:
                self.istemci(SahteGoogle(api_kodu=kod, api_mesaji="The caller does not have permission")).yaz(KIMLIK, komisyon_ornegi())
            self.assertIn("arac@proje.iam.gserviceaccount.com", str(h.exception))
            self.assertIn("Düzenleyen", str(h.exception))

    def test_api_kapaliysa_soylenir(self):
        with self.assertRaises(SheetsHatasi) as h:
            self.istemci(SahteGoogle(api_kodu=403, api_mesaji="Google Sheets API has not been used in project 1 before or it is disabled.")).yaz(KIMLIK, komisyon_ornegi())
        self.assertIn("Etkinleştir", str(h.exception))

    def test_gecersiz_anahtar_jeton_alamaz(self):
        with self.assertRaises(SheetsHatasi):
            Istemci(self.anahtar, SahteGoogle()).yaz(KIMLIK, komisyon_ornegi())  # private_key "x" çözülemez

    def test_hata_sayimi_yalnizca_yazilan_sekmeleri_sorar(self):
        google = SahteGoogle()
        self.istemci(google).yaz(KIMLIK, komisyon_ornegi())
        adres = unquote(next(a for y, a, _, _ in google.istekler if "effectiveValue" in a))
        self.assertIn("ranges='Komisyon'", adres)
        self.assertNotIn("Sayfa1", adres)


if __name__ == "__main__":
    unittest.main()
