"""Çalıştırmak için: python -m unittest -v"""

import contextlib
import io
import tempfile
import unittest
import zipfile
from datetime import date, timedelta
from pathlib import Path
from xml.dom import minidom

from agent import main as _main
from analiz import _fiyat_araligi, _ortak_ad, tedarik_gruplari, tedarik_sayilari
from analiz import (Aday, adaylar, alan_adi, inceleme_baglantilari, aylik_satis, cok_satanlar, degerlendir, derinlesti, digerleri, guncel_kaynak_sayisi, kar_hesabi,
                    kaynak_sayisi, rekabet, riskler, satis_gucu, sirala, yukselenler, yukselis)
from okuyucu import BASLIKLAR, OkumaHatasi, adet, degisim, gun, oku, sayi, sira, tarih, trend
from rapor import dosya
from rapor_html import sayfa, tarih_yaz

ORNEK = str(Path(__file__).parent / "ornek" / "ornek_adaylar.csv")
SABLON = str(Path(__file__).parent / "ornek" / "sablon.csv")
BUGUN = date(2026, 10, 12)
YAKIN, ESKI = BUGUN - timedelta(days=20), BUGUN - timedelta(days=200)
UC_KAYNAK = ["https://a.example/x", "https://b.example/y", "https://c.example/z"]


def main(argv):
    """Aracın komut satırını çalıştırır; yazdıklarını döndürür ki test çıktısı sade kalsın."""
    cikti, hata = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        kod = _main(argv)
    return kod, cikti.getvalue(), hata.getvalue()


def csv_yaz(klasor, metin, ad="liste.csv"):
    yol = Path(klasor) / ad
    yol.write_text(metin, encoding="utf-8")
    return str(yol)


def guclu(**ek):
    """Bütün koşulları sağlayan, 'Öncelikli' çıkan ürün; testler tek tek koşul bozar."""
    alanlar = dict(ad="Katlanır raf", kaynaklar=UC_KAYNAK, kaynak_tarihleri=[YAKIN, YAKIN, None], satis_sirasi=10, yorum=5000,
                   son_satis=2000, son_satis_gun=7, toplam_satis=20_000, tr_satici=2, tr_kontrol="satıcı",
                   maliyet=100.0, satis_fiyati=300.0, komisyon=18.0, kargo=50.0)
    alanlar.update(ek)
    return Aday(**alanlar)


def d(aday, komisyon=None, kargo=None):
    return degerlendir(aday, BUGUN, komisyon, kargo)


class SatisGucu(unittest.TestCase):
    def test_sinirlar(self):
        self.assertEqual(satis_gucu(Aday("x", satis_sirasi=1)).puan, 100)
        self.assertEqual(satis_gucu(Aday("x", satis_sirasi=10_000)).puan, 0)
        self.assertEqual(satis_gucu(Aday("x", yorum=100)).puan, 0)
        self.assertEqual(satis_gucu(Aday("x", yorum=100_000)).puan, 100)
        self.assertEqual(satis_gucu(Aday("x", son_satis=100_000, son_satis_gun=30)).puan, 100)
        self.assertEqual(satis_gucu(Aday("x", son_satis=500, son_satis_gun=30)).puan, 0)
        self.assertEqual(satis_gucu(Aday("x", toplam_satis=1_000_000)).puan, 100)

    def test_bilinmeyen_isaret_puani_dusurmez_kaniti_dusurur(self):
        tek = satis_gucu(Aday("x", satis_sirasi=1))
        uc = satis_gucu(Aday("x", satis_sirasi=1, yorum=100_000, son_satis=100_000, son_satis_gun=30))
        self.assertEqual((tek.puan, tek.kanit), (100, "zayıf"))
        self.assertEqual((uc.puan, uc.kanit), (100, "güçlü"))
        self.assertIn("yorum sayısı", tek.eksikler)

    def test_hicbir_isaret_yoksa_puan_yok(self):
        p = satis_gucu(Aday("x"))
        self.assertIsNone(p.puan)
        self.assertEqual(p.kanit, "yok")

    def test_satis_30_gune_oranlanir(self):
        self.assertEqual(aylik_satis(Aday("x", son_satis=700, son_satis_gun=7)), 3000)
        self.assertIn("yaklaşık 3.000", satis_gucu(Aday("x", son_satis=700, son_satis_gun=7)).aciklamalar[0])

    def test_donemi_bilinmeyen_satis_adedi_puana_girmez(self):
        p = satis_gucu(Aday("x", son_satis=9000))
        self.assertIsNone(p.puan)
        self.assertIn("satış adedinin kaç güne ait olduğu", p.eksikler)


class Yukselis(unittest.TestCase):
    def test_guncel_yazilar_site_basina_bir_kez_sayilir(self):
        a = Aday("x", kaynaklar=["a.example/1", "a.example/2", "b.example/1", "c.example/1"], kaynak_tarihleri=[YAKIN, YAKIN, YAKIN, ESKI])
        self.assertEqual(guncel_kaynak_sayisi(a, BUGUN), 2)

    def test_yuz_yirmi_gun_siniri(self):
        tam = Aday("x", kaynaklar=["a.example/1"], kaynak_tarihleri=[BUGUN - timedelta(days=120)])
        gecmis = Aday("x", kaynaklar=["a.example/1"], kaynak_tarihleri=[BUGUN - timedelta(days=121)])
        self.assertEqual((guncel_kaynak_sayisi(tam, BUGUN), guncel_kaynak_sayisi(gecmis, BUGUN)), (1, 0))
        self.assertEqual(yukselis(gecmis, BUGUN).puan, 0)

    def test_tarihsiz_ve_gelecek_tarihli_kaynak_sayilmaz(self):
        tarihsiz = Aday("x", kaynaklar=UC_KAYNAK, kaynak_tarihleri=[None, None, None])
        gelecek = Aday("x", kaynaklar=["a.example/1"], kaynak_tarihleri=[BUGUN + timedelta(days=3)])
        for a in (tarihsiz, gelecek):
            self.assertIsNone(guncel_kaynak_sayisi(a, BUGUN))
            self.assertIsNone(yukselis(a, BUGUN).puan)

    def test_ivme_satisin_son_doneme_dusen_payidir(self):
        yeni = yukselis(Aday("x", son_satis=1760, son_satis_gun=7, toplam_satis=20_150), BUGUN)
        yerlesik = yukselis(Aday("x", son_satis=1340, son_satis_gun=7, toplam_satis=249_080), BUGUN)
        self.assertEqual(yeni.parcalar["İvme"], (39, 40))
        self.assertEqual(yerlesik.parcalar["İvme"], (0, 40))
        self.assertIn("%37,4", yeni.aciklamalar[0])

    def test_pay_yuzde_yuzu_gecemez(self):
        p = yukselis(Aday("x", son_satis=4000, son_satis_gun=7, toplam_satis=12_000), BUGUN)
        self.assertIn("%100,0", p.aciklamalar[0])

    def test_kucuk_satis_tabaninda_yukselis_olculmez(self):
        # Küçük ilan: haftada 405, toplam 6.000 adet. Oran yüksek çıkar ama taban küçük.
        p = yukselis(Aday("x", son_satis=405, son_satis_gun=7, toplam_satis=6000), BUGUN)
        self.assertNotIn("İvme", p.parcalar)
        self.assertIsNone(p.puan)
        self.assertIn("satışın ne kadarının yeni olduğu (satış tabanı küçük)", p.eksikler)
        self.assertIn("10.000 adedin altında", p.aciklamalar[0])
        az = yukselis(Aday("x", son_satis=40, son_satis_gun=7, yorum=20), BUGUN)
        self.assertNotIn("İvme", az.parcalar)

    def test_toplam_haftalik_rakama_esitse_bilinmiyor_sayilir(self):
        # Bazı listeler toplamı bilinmeyen üründe haftalık rakamı toplam diye de yazar.
        a = Aday("x", son_satis=8000, son_satis_gun=7, toplam_satis=8000)
        self.assertNotIn("İvme", yukselis(a, BUGUN).parcalar)
        self.assertNotIn("Toplam satış", satis_gucu(a).parcalar)
        self.assertEqual(aylik_satis(a), 8000 * 30 / 7)

    def test_onceki_aya_gore_satis_artisi(self):
        cok = dict(son_satis=5000, son_satis_gun=30)
        hizli = yukselis(Aday("x", satis_degisim=60.0, **cok), BUGUN)
        orta = yukselis(Aday("x", satis_degisim=35.0, **cok), BUGUN)
        dusen = yukselis(Aday("x", satis_degisim=-20.0, **cok), BUGUN)
        self.assertEqual((hizli.parcalar["Satış artışı"], orta.parcalar["Satış artışı"], dusen.parcalar["Satış artışı"]), ((30, 30), (15, 30), (0, 30)))
        self.assertIn("%35,0 arttı", orta.aciklamalar[0])
        self.assertIn("%20,0 azaldı", dusen.aciklamalar[0])
        sonuc = d(Aday("x", kaynaklar=UC_KAYNAK, son_satis=10_000, son_satis_gun=30, yorum=43, satis_degisim=66.7))  # yeni ürün
        self.assertEqual(sonuc.sinif, "Yeni yükselen")
        eski = yukselis(Aday("x", satis_degisim=60.0, veri_tarihi=BUGUN - timedelta(days=190), **cok), BUGUN)
        self.assertNotIn("Satış artışı", eski.parcalar)

    def test_kucuk_satista_artis_yuzdesi_olculmez(self):
        # Gerçek denemeden: ayda 200 adet satan ürün +%100 ile listenin başına çıkmıştı.
        kucuk = d(Aday("Tayt", kaynaklar=UC_KAYNAK, son_satis=200, son_satis_gun=30, yorum=70, satis_degisim=100.0))
        self.assertNotIn("Satış artışı", kucuk.yukselis.parcalar)
        self.assertEqual(kucuk.sinif, "Öne çıkmadı")
        self.assertIn("küçük rakamlarda yüzde yanıltır", " ".join(kucuk.yukselis.aciklamalar))
        self.assertNotIn("Satış artışı", yukselis(Aday("x", satis_degisim=80.0), BUGUN).parcalar)  # satış adedi bilinmiyor

    def test_ayni_yukselis_puaninda_cok_satan_once_gelir(self):
        az = Aday("Az satan", kaynaklar=UC_KAYNAK, son_satis=2500, son_satis_gun=30, satis_degisim=80.0)
        cok_satan = Aday("Çok satan", kaynaklar=UC_KAYNAK, son_satis=20_000, son_satis_gun=30, satis_degisim=80.0)
        self.assertEqual([x.aday.ad for x in yukselenler(sirala([az, cok_satan], BUGUN))], ["Çok satan", "Az satan"])

    def test_toplam_satis_yoksa_yorum_oranina_bakilir(self):
        yeni = yukselis(Aday("x", son_satis=40_000, son_satis_gun=30, yorum=2200), BUGUN)
        eski = yukselis(Aday("x", son_satis=30_000, son_satis_gun=30, yorum=126_000), BUGUN)
        self.assertEqual((yeni.parcalar["Yeni ürün"], eski.parcalar["Yeni ürün"]), ((20, 20), (0, 20)))
        self.assertIn("tek başına yükseliş sayılmaz", yeni.aciklamalar[0])
        self.assertNotIn("İvme", yeni.parcalar)

    def test_yorumuna_gore_cok_satmak_tek_basina_yukselen_yapmaz(self):
        # Gerçek denemeden: 10.000 satış, 779 yorum, artış rakamı yok; listenin başına "yükseliş 100" ile çıkmıştı.
        tahta = d(Aday("Bambu kesme tahtası", kaynaklar=UC_KAYNAK, son_satis=10_000, son_satis_gun=30, yorum=779))
        self.assertNotIn(tahta.sinif, ("Yeni yükselen", "Çok satan ve yükselen"))
        self.assertIn("satışının arttığını gösteren rakam yok", tahta.sinif_gerekce)
        artan = d(Aday("Bambu kesme tahtası", kaynaklar=UC_KAYNAK, son_satis=10_000, son_satis_gun=30, yorum=779, satis_degisim=66.7))
        self.assertIn(artan.sinif, ("Yeni yükselen", "Çok satan ve yükselen"))

    def test_eski_satis_rakami_yukselis_sayilmaz(self):
        # Gerçek kullanımdan: Nisan tarihli satış rakamı Ekim raporunda "yükselen" çıkmıştı.
        yeni = dict(son_satis=10_000, son_satis_gun=30, yorum=1000, satis_degisim=50.0)
        guncel = yukselis(Aday("x", veri_tarihi=BUGUN - timedelta(days=60), **yeni), BUGUN)
        eski = yukselis(Aday("x", veri_tarihi=BUGUN - timedelta(days=190), **yeni), BUGUN)
        self.assertIn("Satış artışı", guncel.parcalar)
        self.assertEqual(eski.parcalar, {})
        self.assertIn("güncel satış rakamı", eski.eksikler)
        self.assertEqual(d(Aday("x", kaynaklar=UC_KAYNAK, satis_sirasi=1, veri_tarihi=BUGUN - timedelta(days=190), **yeni)).sinif, "Çok satan")

    def test_arama_ilgisinin_yonu(self):
        self.assertEqual(yukselis(Aday("x", trend="yükseliyor"), BUGUN).puan, 100)
        self.assertEqual(yukselis(Aday("x", trend="düşüyor"), BUGUN).puan, 0)
        self.assertIn("arama ilgisinin yönü (Google Trends)", yukselis(Aday("x"), BUGUN).eksikler)


class Siniflar(unittest.TestCase):
    def sinif(self, **alanlar):
        return d(Aday("x", **alanlar)).sinif

    def test_alti_sinif(self):
        hizli = dict(son_satis=2000, son_satis_gun=7, toplam_satis=20_000)
        self.assertEqual(self.sinif(kaynaklar=UC_KAYNAK, satis_sirasi=5, **hizli), "Çok satan ve yükselen")
        self.assertEqual(self.sinif(kaynaklar=UC_KAYNAK, son_satis=600, son_satis_gun=7, toplam_satis=10_000), "Yeni yükselen")
        self.assertEqual(self.sinif(kaynaklar=UC_KAYNAK, kaynak_tarihleri=[YAKIN, YAKIN, YAKIN]), "Yükseliş adayı")
        self.assertEqual(self.sinif(kaynaklar=UC_KAYNAK, satis_sirasi=3, yorum=90_000), "Çok satan")
        self.assertEqual(self.sinif(kaynaklar=UC_KAYNAK, satis_sirasi=5000, yorum=150), "Öne çıkmadı")
        self.assertEqual(self.sinif(kaynaklar=UC_KAYNAK), "Kanıt yetersiz")

    def test_kaynaksiz_urun_rakami_ne_olursa_olsun_kanit_yetersiz(self):
        sonuc = d(Aday("x", satis_sirasi=1, yorum=200_000, son_satis=9000, son_satis_gun=7, toplam_satis=10_000))
        self.assertEqual(sonuc.sinif, "Kanıt yetersiz")
        self.assertIn("Kaynak bağlantısı yok", sonuc.sinif_gerekce)

    def test_yalnizca_guncel_yaziya_dayanan_yukselis_aday_kalir(self):
        sonuc = d(Aday("x", kaynaklar=UC_KAYNAK, kaynak_tarihleri=[YAKIN, YAKIN, YAKIN]))
        self.assertEqual((sonuc.sinif, sonuc.yukselis.puan), ("Yükseliş adayı", 100))
        self.assertIn("satış rakamı görülemedi", sonuc.sinif_gerekce)
        tek = d(Aday("x", kaynaklar=UC_KAYNAK, kaynak_tarihleri=[YAKIN, None, None]))
        self.assertEqual(tek.sinif, "Yükseliş adayı")
        eski = d(Aday("x", kaynaklar=UC_KAYNAK, kaynak_tarihleri=[ESKI, None, None]))
        self.assertEqual(eski.sinif, "Kanıt yetersiz" if eski.yukselis.puan is None else "Öne çıkmadı")

    def test_az_yorumu_olan_urun_yazida_geciyorsa_izleme_listesinde_kalir(self):
        # Gerçek bir rakam eklemek ürünü izleme listesinden düşürmemeli.
        sonuc = d(Aday("x", kaynaklar=UC_KAYNAK, kaynak_tarihleri=[YAKIN, YAKIN, YAKIN], yorum=300))
        self.assertEqual(sonuc.sinif, "Yükseliş adayı")
        yerlesik = d(Aday("x", kaynaklar=UC_KAYNAK, kaynak_tarihleri=[YAKIN, None, None], son_satis=300, son_satis_gun=7, toplam_satis=90_000))
        self.assertEqual(yerlesik.sinif, "Öne çıkmadı")  # satış rakamı yerleşik olduğunu gösteriyorsa aday sayılmaz

    def test_bir_aydan_yeni_urun_satmadigi_adetle_cok_satan_sayilmaz(self):
        # Gerçek denemeden: son 7 günde 4.560, toplam 7.570. 30 güne oranlanınca 19.543 çıkar; toplamı aşamaz.
        a = Aday("File", kaynaklar=UC_KAYNAK, son_satis=4560, son_satis_gun=7, toplam_satis=7570)
        self.assertEqual(aylik_satis(a), 7570)
        sonuc = d(a)
        self.assertEqual(sonuc.sinif, "Öne çıkmadı")  # toplamı 10.000 adedin altında; yükselişi de ölçülmez
        self.assertIn("bir aydan yeni bir ürün", " ".join(sonuc.satis.aciklamalar))

    def test_eski_cok_satan_yukselen_sayilmaz(self):
        sonuc = d(Aday("Terazi", kaynaklar=UC_KAYNAK, satis_sirasi=4, yorum=177_000, son_satis=1340, son_satis_gun=7, toplam_satis=249_080))
        self.assertEqual(sonuc.sinif, "Çok satan")
        self.assertIn("yerleşik", sonuc.sinif_gerekce)

    def test_listeler(self):
        sonuc = sirala(oku(ORNEK), BUGUN)
        self.assertEqual([x.aday.ad for x in yukselenler(sonuc)],
                         ["Buzlu içecek (slush) bardağı", "Titanyum kesme tahtası", "Hava geçirmez saklama kabı seti (40 parça)"])
        self.assertEqual(cok_satanlar(sonuc)[0].aday.ad, "Yalıtımlı pipetli bardak (1,2 litre)")
        self.assertEqual((len(yukselenler(sonuc)), len(cok_satanlar(sonuc)), len(adaylar(sonuc)), len(digerleri(sonuc))), (3, 6, 3, 1))
        terazi = next(x for x in sonuc if x.aday.ad == "Dijital mutfak terazisi")
        self.assertEqual((terazi.sinif, terazi.yukselis.puan), ("Çok satan", 0))
        puanlar = [x.satis.puan for x in cok_satanlar(sonuc)]
        self.assertEqual(puanlar, sorted(puanlar, reverse=True))


class RekabetVeKar(unittest.TestCase):
    def test_rekabet_esikleri(self):
        for n, beklenen in ((None, "bilinmiyor"), (0, "bulunamadı"), (5, "az satıcı"), (6, "orta"), (20, "orta"), (21, "kalabalık")):
            self.assertEqual(rekabet(Aday("x", tr_satici=n, tr_kontrol="satıcı"))[0], beklenen)

    def test_asistanin_sayimi_kaba_ipucu_diye_isaretlenir(self):
        self.assertIn("kaba ipucudur", rekabet(Aday("x", tr_satici=3, tr_kontrol="asistan"))[1])
        self.assertNotIn("kaba ipucudur", rekabet(Aday("x", tr_satici=3, tr_kontrol="satıcı"))[1])

    def test_kar_hesabi(self):
        k = kar_hesabi(guclu())
        self.assertAlmostEqual(k.net, 300 - 100 - 54 - 50)
        self.assertAlmostEqual(k.marj, 32.0)
        self.assertEqual(k.eksikler, [])

    def test_maliyet_ya_da_fiyat_yoksa_hesaplanmaz(self):
        self.assertIsNone(kar_hesabi(guclu(maliyet=None)))
        self.assertIsNone(kar_hesabi(guclu(satis_fiyati=None)))

    def test_fiyat_yoksa_turkiyede_gorulen_fiyat_kullanilir(self):
        k = kar_hesabi(guclu(satis_fiyati=None, tr_fiyat=250.0))
        self.assertEqual((k.fiyat, k.fiyat_kaynagi), (250.0, "Türkiye'de görülen fiyat"))

    def test_varsayilan_komisyon_ve_kargo(self):
        k = kar_hesabi(guclu(komisyon=None, kargo=None), 20, 40)
        self.assertAlmostEqual(k.net, 300 - 100 - 60 - 40)
        self.assertEqual(kar_hesabi(guclu(komisyon=None, kargo=None)).eksikler, ["komisyon", "kargo"])


class RiskUyarilari(unittest.TestCase):
    def duzeyler(self, ad, kategori="", marka=""):
        return [r.duzey for r in riskler(Aday(ad, kategori=kategori, marka=marka))]

    def test_yasak_izin_dikkat(self):
        self.assertEqual(self.duzeyler("Tek kullanımlık elektronik sigara")[0], "yasak")
        self.assertEqual(self.duzeyler("C vitaminli yüz serumu")[0], "izin")
        self.assertEqual(self.duzeyler("ŞARJLI MASA VANTİLATÖRÜ"), ["dikkat"])
        self.assertEqual(self.duzeyler("Ahşap oyun kartı kutusu"), [])
        self.assertEqual(self.duzeyler("Çok bıçaklı doğrayıcı"), ["dikkat"])  # gıdayla temas; bıçak uyarısı değil
        self.assertEqual([r.konu for r in riskler(Aday("Şef bıçağı"))], ["Bıçak ya da lazer"])
        self.assertEqual([r.konu for r in riskler(Aday("Tezgah üstü buz makinesi"))], ["Elektrikli ya da pilli ürün"])

    def test_kategori_ve_marka_da_taranir(self):
        self.assertEqual(self.duzeyler("Renkli bloklar", kategori="Oyuncak"), ["dikkat"])
        self.assertEqual(self.duzeyler("Raf", marka="Bir Marka"), ["dikkat"])

    def test_kelime_ortasindaki_eslesme_sayilmaz(self):
        # "led" kelimesi "tabledot" içinde geçiyor diye elektrikli ürün sayılmamalı
        self.assertEqual(self.duzeyler("Tabledot tepsisi"), [])
        self.assertEqual(self.duzeyler("LED'li ayna"), ["dikkat"])

    def test_icecek_bardagi_gida_sayilmaz(self):
        self.assertEqual([r.konu for r in riskler(Aday("Buzlu içecek (slush) bardağı"))], ["Gıdayla temas eden ürün"])
        self.assertEqual([r.konu for r in riskler(Aday("Simli enerji içeceği temalı termos bardak"))], ["Gıdayla temas eden ürün"])
        self.assertEqual(self.duzeyler("Dürüm kapatma (tost) aparatı"), [])
        self.assertEqual(self.duzeyler("Çamaşır makinesi için ayakkabı yıkama filesi"), [])
        self.assertEqual(self.duzeyler("Dönen makyaj ve bakım ürünü düzenleyici"), [])
        self.assertEqual(self.duzeyler("Makyaj seti")[0], "izin")
        self.assertEqual([r.konu for r in riskler(Aday("Tek kullanımlık nem alıcı"))], ["Kimyasal içerikli ürün"])

    def test_evcil_hayvan_urunleri(self):
        for ad in ("Kuru köpek maması", "Doğal köpek ödülü karma kutusu", "Çıtır kedi ödül maması"):
            self.assertEqual(riskler(Aday(ad))[0].konu, "Evcil hayvan maması ya da ödülü", ad)
        self.assertEqual(riskler(Aday("Evcil hayvan göz damlası"))[0].konu, "Veteriner ürünü")
        self.assertEqual(riskler(Aday("Kulübe dezenfektanı 5 litre"))[0].duzey, "izin")
        self.assertEqual([r.konu for r in riskler(Aday("Ödül doldurulan köpek oyuncağı"))], ["Oyuncak ve bebek ürünü"])
        self.assertEqual(d(guclu(ad="Doğal köpek ödülü karma kutusu")).karar, "İncelenebilir")


class Karar(unittest.TestCase):
    def test_butun_kosullar_saglaninca_oncelikli(self):
        sonuc = d(guclu())
        self.assertEqual(sonuc.karar, "Öncelikli")
        self.assertIn("kâr marjı %32,0", sonuc.gerekce)

    def test_her_kosul_tek_basina_onceligi_dusurur(self):
        for ek, parca in ((dict(tr_satici=30), "rekabet kalabalık"), (dict(tr_satici=None, tr_kontrol=""), "rekabete bakılmadı"),
                          (dict(tr_kontrol="asistan"), "kendi pazaryerinizde doğrulamadınız"),
                          (dict(maliyet=None), "kâr hesaplanamadı"), (dict(maliyet=180.0), "kâr marjı %20'nin altında"),
                          (dict(komisyon=None), "komisyon girilmedi"), (dict(ad="Gece serumu"), "izin ya da bildirim")):
            sonuc = d(guclu(**ek))
            self.assertEqual(sonuc.karar, "İncelenebilir", ek)
            self.assertIn(parca, sonuc.gerekce)

    def test_zarar_eden_ve_yasak_urun_elenir(self):
        self.assertEqual(d(guclu(maliyet=260.0)).karar, "Elenir")
        self.assertIn("zarar", d(guclu(maliyet=260.0)).gerekce)
        self.assertEqual(d(guclu(ad="Elektronik sigara")).karar, "Elenir")

    def test_one_cikmayan_urun_oncelikli_olamaz(self):
        sonuc = d(guclu(satis_sirasi=5000, yorum=150, son_satis=None, toplam_satis=None, kaynak_tarihleri=[ESKI, ESKI, ESKI]))
        self.assertEqual((sonuc.sinif, sonuc.karar), ("Öne çıkmadı", "Öne çıkmadı"))

    def test_turkiye_ve_maliyet_yoksa_karar_gosterilmez(self):
        self.assertFalse(derinlesti([d(Aday("x", kaynaklar=UC_KAYNAK, satis_sirasi=3))]))
        self.assertTrue(derinlesti([d(guclu())]))


class Okuyucu(unittest.TestCase):
    def test_sayi_ve_adet(self):
        self.assertEqual(sayi("1.299,90 TL"), 1299.9)
        self.assertEqual([sira(x) for x in ("1.2", "5.8", "14", "12.500", "0,4", "ilk 10", "")], [1, 6, 14, 12500, 1, None, None])
        self.assertEqual([adet(x) for x in ("12500", "12.500", "2,4 milyon", "850 bin", "1.2M", "89K", "1.76K", "abc", "-5", "")],
                         [12500, 12500, 2_400_000, 850_000, 1_200_000, 89_000, 1760, None, None, None])

    def test_tarih(self):
        for metin, beklenen in (("2026-10-01", date(2026, 10, 1)), ("2026-10", date(2026, 10, 1)), ("01.10.2026", date(2026, 10, 1)),
                                ("1 Ekim 2026", date(2026, 10, 1)), ("Eylül 2026", date(2026, 9, 1)), ("Oct. 2, 2026", date(2026, 10, 2)),
                                ("2 October 2026", date(2026, 10, 2)), ("Ağustos 15, 2026", date(2026, 8, 15))):
            self.assertEqual(tarih(metin), beklenen, metin)
        self.assertEqual((tarih_yaz(tarih("2026-09")), tarih_yaz(tarih("Eylül 2026")), tarih_yaz(tarih("2026-09-01"))),
                         ("Eylül 2026", "Eylül 2026", "1 Eylül 2026"))
        for metin in ("10/02/2026", "-", "dün", "2026-13-01", "31.02.2026", ""):
            self.assertIsNone(tarih(metin), metin)

    def test_yuzde_degisim(self):
        self.assertEqual([degisim(x) for x in ("33.3", "%33,3", "▲ 33.3%", "+12", "▼ 8%", "-8", "", "yok", "0")],
                         [33.3, 33.3, 33.3, 12.0, -8.0, -8.0, None, None, 0.0])

    def test_donem_ve_yon(self):
        self.assertEqual([gun(x) for x in ("7", "7 gün", "1 hafta", "2 hafta", "ay", "", "abc", "0")], [7, 7, 7, 14, 30, None, None, None])
        self.assertEqual([trend(x) for x in ("Yükseliyor", "düz", "DÜŞÜYOR", "artıyor", "?", "")],
                         ["yükseliyor", "düz", "düşüyor", "yükseliyor", None, None])

    def test_ornek_ve_sablon_okunur(self):
        self.assertEqual(len(oku(ORNEK)), 12)
        ilk = oku(SABLON)[0]
        self.assertEqual((ilk.son_satis, ilk.son_satis_gun, ilk.toplam_satis, ilk.trend, ilk.tr_kontrol), (900, 7, 14000, "yükseliyor", "satıcı"))
        self.assertEqual(Path(ORNEK).read_text(encoding="utf-8-sig").splitlines()[0], BASLIKLAR)

    def test_kaynak_tarihleri_kaynakla_ayni_sirada_eslesir(self):
        with tempfile.TemporaryDirectory() as k:
            (a,) = oku(csv_yaz(k, "ad;kaynak;kaynak_tarihi;tr_kaynak\nRaf;a.example/x b.example/y c.example/z;- 2026-09-20;https://tr.example/ara\n"))
        self.assertEqual(a.kaynak_tarihleri, [None, date(2026, 9, 20), None])
        self.assertEqual((kaynak_sayisi(a.kaynaklar), a.tr_kaynaklar), (3, ["https://tr.example/ara"]))

    def test_turkiye_sayisini_kimin_gordugu(self):
        with tempfile.TemporaryDirectory() as k:
            a, b, c = oku(csv_yaz(k, "ad;tr_satici;tr_kontrol\nA;3;Satıcı\nB;3;\nC;;satıcı\n"))
        self.assertEqual((a.tr_kontrol, b.tr_kontrol, c.tr_kontrol), ("satıcı", "asistan", ""))

    def test_yalnizca_ad_yeterli_virgullu_dosya_da_okunur(self):
        with tempfile.TemporaryDirectory() as k:
            (a,) = oku(csv_yaz(k, "ad,yorum\nRaf,1200\n"))
        self.assertEqual((a.ad, a.yorum, a.kaynaklar), ("Raf", 1200, []))

    def test_hatalar(self):
        with tempfile.TemporaryDirectory() as k:
            for metin, parca in (("urun_kodu;x\n1;2\n", "'ad' sütunu"), ("ad;yorum\n;5\n", "adı yazılı ürün"),
                                 ("ad;yorum\nRaf;5;fazla;hücre\n", "fazla sütun")):
                with self.assertRaises(OkumaHatasi) as h:
                    oku(csv_yaz(k, metin))
                self.assertIn(parca, str(h.exception))
            with self.assertRaises(OkumaHatasi):
                oku(Path(k) / "yok.csv")
            with self.assertRaises(OkumaHatasi):
                oku(csv_yaz(k, "ad\nRaf\n", "liste.txt"))

    def test_urun_kimligi_ve_inceleme_baglantilari(self):
        with tempfile.TemporaryDirectory() as k:
            (a,) = oku(csv_yaz(k, "ad;orijinal_ad;urun_link;yurtdisi_fiyat\nHamile yastığı (U şeklinde);U Shaped Pregnancy Pillow;"
                                  "https://www.amazon.com/dp/B0TEST1234;$32.99\n"))
        self.assertEqual((a.orijinal_ad, a.urun_linkleri, a.yurtdisi_fiyat),
                         ("U Shaped Pregnancy Pillow", ["https://www.amazon.com/dp/B0TEST1234"], "$32.99"))
        b = inceleme_baglantilari(a)
        self.assertEqual(b["Ürünü gör"][0], ("Ürün sayfası (amazon.com)", "https://www.amazon.com/dp/B0TEST1234"))
        self.assertIn(("Amazon'da ara", "https://www.amazon.com/s?k=U+Shaped+Pregnancy+Pillow"), b["Ürünü gör"])
        self.assertEqual(b["Türkiye'de bak"][0], ("Trendyol", "https://www.trendyol.com/sr?q=Hamile+yast%C4%B1%C4%9F%C4%B1"))
        adsiz = inceleme_baglantilari(Aday("Süt köpürtücü", urun_linkleri=["javascript:alert(1.0)"]))
        self.assertEqual([e for e, _ in adsiz["Ürünü gör"]], ["Görseller"])  # zararlı adres atılır; kaynak adı yoksa Türkçe adla aranır
        self.assertEqual(adsiz["Çin'de tedarik"], [])

    def test_cin_tedarik_baglantilari(self):
        a = Aday("Titanyum kesme tahtası", orijinal_ad="Titanium Cutting Board", cince_ad="钛砧板", tedarik_fiyat="$7.90-9.90", tedarik_moq="500", tedarikci="Zhejiang",
                 tedarik_linkleri=["https://detail.1688.example/offer/1.html", "javascript:alert(1.0)"])
        cin = dict(inceleme_baglantilari(a)["Çin'de tedarik"])
        self.assertEqual(cin["Tedarikçi sayfası (detail.1688.example)"], "https://detail.1688.example/offer/1.html")
        self.assertTrue(cin["1688"].startswith("https://s.1688.com/selloffer/offer_search.htm?keywords=%"))  # GBK kodlu
        self.assertNotIn("%E9%92%9B", cin["1688"])  # UTF-8 değil
        self.assertEqual(cin["Taobao"], "https://s.taobao.com/search?q=%E9%92%9B%E7%A0%A7%E6%9D%BF")
        self.assertEqual(cin["Alibaba"], "https://www.alibaba.com/trade/search?SearchText=Titanium+Cutting+Board")
        self.assertEqual(cin["Made-in-China"], "https://www.made-in-china.com/multi-search/Titanium%2BCutting%2BBoard/F1/1.html")
        self.assertEqual(cin["AliExpress"], "https://www.aliexpress.com/w/wholesale-Titanium-Cutting-Board.html")
        uzun = Aday("x", orijinal_ad="Momcozy U Shaped Pregnancy Pillow 57 inch, Full Body & Maternity Support | Grey (2026)")
        self.assertEqual(dict(inceleme_baglantilari(uzun)["Çin'de tedarik"])["Alibaba"],
                         "https://www.alibaba.com/trade/search?SearchText=Momcozy+U+Shaped+Pregnancy+Pillow+57")
        self.assertEqual(len([e for e in cin if e.startswith("Tedarikçi sayfası")]), 1)  # zararlı adres atıldı
        self.assertNotIn("1688", dict(inceleme_baglantilari(Aday("x", orijinal_ad="Board"))["Çin'de tedarik"]))  # Çince adı yok

    def test_alan_adi(self):
        self.assertEqual(alan_adi("https://www.Ornek.com:443/x?y=1"), "ornek.com")
        self.assertEqual(kaynak_sayisi(["a.example/1", "https://www.a.example/2"]), 1)


class KomutSatiri(unittest.TestCase):
    def test_ornek_veri(self):
        kod, cikti, hata = main(["tara", ORNEK, "--alan", "Mutfak ürünleri", "--tarih", "2026-10-12"])
        self.assertEqual((kod, hata), (0, ""))
        for parca in ("ÜRÜN ARAŞTIRMA RAPORU — Mutfak ürünleri — 12 Ekim 2026 — 12 ürün, 6 kaynak site", "YÜKSELENLER — 3 ürün",
                      "ÇOK SATANLAR — 6 ürün (1 tanesi yükselenler listesinde de var)", "YAZILARDA GEÇENLER — 3 ürün", "ÖNE ÇIKMAYANLAR — 1 ürün",
                      "TÜRKİYE, KÂR VE KARAR — 6 ürün", "Diğer 6 ürün için Türkiye ve maliyet bilgisi girilmedi", "217,18 TL", "-%24,4",
                      "AYRINTI — öne çıkan 8 ürün",
                      "1 üründe kaynak bağlantısı yok", "satış garantisi değildir"):
            self.assertIn(parca, cikti)
        self.assertEqual(cikti.count("  Öncelikli\n"), 2)
        self.assertEqual(cikti.count("  Elenir\n"), 1)

    def test_ayrinti_secenegi_butun_urunleri_yazar(self):
        kisa = main(["tara", ORNEK, "--tarih", "2026-10-12"])[1]
        uzun = main(["tara", ORNEK, "--tarih", "2026-10-12", "--ayrinti"])[1]
        self.assertNotIn("Katlanır silikon süzgeç — Kanıt yetersiz\n", kisa)
        self.assertIn("12. Katlanır silikon süzgeç — Kanıt yetersiz\n", uzun)

    def test_degerlendir_ayni_isi_yapar(self):
        self.assertEqual(main(["tara", ORNEK, "--tarih", "2026-10-12"])[1], main(["degerlendir", ORNEK, "--tarih", "2026-10-12"])[1])

    def test_turkiye_bilgisi_yokken_karar_yazilmaz(self):
        with tempfile.TemporaryDirectory() as k:
            kod, cikti, _ = main(["tara", csv_yaz(k, "ad;kaynak;satis_sirasi;yorum\nRaf;a.example/x;3;90000\n")])
        self.assertEqual(kod, 0)
        self.assertNotIn("TÜRKİYE, KÂR VE KARAR", cikti)
        self.assertNotIn("Karar ", cikti)
        self.assertIn("Türkiye'deki rekabet, kâr ve karar hesaplanmadı", cikti)

    def test_uyari_notlari(self):
        with tempfile.TemporaryDirectory() as k:
            yol = csv_yaz(k, "ad;kaynak;kaynak_tarihi;son_satis\nRaf;a.example/x;2027-01-01;500\n")
            kod, cikti, _ = main(["tara", yol, "--tarih", "2026-10-12", "--komisyon", "18"])
        self.assertIn("kaç güne ait olduğu (son_satis_gun) yazılmamış", cikti)
        self.assertIn("rapor tarihinden sonraya ait kaynak tarihi", cikti)
        self.assertIn("Not: Bu taramada açılamayan kaynaklar: amazon.com", main(["tara", ORNEK, "--acilmayan", "amazon.com"])[1])

    def test_hatali_girdi(self):
        for argv, parca in ((["tara", "yok.csv"], "Dosya bulunamadı"), (["tara", ORNEK, "--tarih", "dün"], "Tarih anlaşılamadı"),
                            (["tara", ORNEK, "--komisyon", "120"], "Komisyon anlaşılamadı"), (["tara", ORNEK, "--kargo", "-5"], "Kargo anlaşılamadı")):
            kod, _, hata = main(argv)
            self.assertEqual(kod, 1)
            self.assertIn(parca, hata)

    def test_dosyalar_kaydedilir_klasor_yoksa_acilir(self):
        with tempfile.TemporaryDirectory() as k:
            kod, cikti, _ = main(["tara", ORNEK, "--tarih", "2026-10-12", "--rapor", str(Path(k) / "yeni" / "rapor"), "--excel", str(Path(k) / "r")])
            self.assertEqual(kod, 0)
            self.assertTrue((Path(k) / "yeni" / "rapor.html").exists())
            self.assertTrue((Path(k) / "r.xlsx").exists())
        self.assertIn("Rapor sayfası kaydedildi", cikti)
        self.assertIn("Excel dosyası kaydedildi", cikti)


class RaporSayfasi(unittest.TestCase):
    def test_bolumler_ve_rakamlar(self):
        html = sayfa(sirala(oku(ORNEK), BUGUN), BUGUN, "Mutfak ürünleri", "amazon.com, tiktok.com")
        for parca in ("<title>Mutfak ürünleri: yurt dışında çok satanlar ve yükselenler</title>", "Rapor tarihi 12 Ekim 2026",
                      "<h2>Yükselenler</h2>", "<h2>Çok satanlar</h2>", "<h2>Yazılarda geçenler</h2>", "<h2>Öne çıkmayanlar</h2>",
                      "en yeni satış verisi 1 Ekim 2026", "1 ürün hem yükselenler hem çok satanlar listesinde", "<h2>Türkiye, kâr ve karar</h2>",
                      "Sıradaki adım: Türkiye kontrolü", "<h2>Yöntem ve sınırlar</h2>", "%37,4", "217,18 TL",
                      "açılamayan kaynaklar: amazon.com, tiktok.com", 'href="https://ornek-dergi.example/viral-mutfak"',
                      "Listedeki adı: Frozen Slushy Squeeze Cup", "Yurt dışı fiyatı: $14.99", "<b>Ürünü gör:</b>", "<b>Çin&#x27;de tedarik:</b>", "<b>Türkiye&#x27;de bak:</b>",
                      "Çin&#x27;de fabrika fiyatı (liste): $1.35-1.80, en az 20 adet (Zhejiang)", "Çince adı: 冰沙杯",
                      'href="https://ornek-videosatis.example/urun/slushy-cup"', 'href="https://www.trendyol.com/sr?q=Titanyum+kesme+tahtas%C4%B1"',
                      "Tek tıkla bakın"):
            self.assertIn(parca, html)
        self.assertNotIn("<script", html.lower())

    def test_urun_fotografi_yalnizca_https_adresinden_gosterilir(self):
        def html(adres):
            return sayfa(sirala([Aday("Raf", kaynaklar=UC_KAYNAK, satis_sirasi=2, gorsel=adres)], BUGUN), BUGUN)
        self.assertIn('<img class="kucuk" src="https://m.media.example/I/81abc.jpg"', html("https://m.media.example/I/81abc.jpg"))
        for kotu in ("http://a.example/x.jpg", "javascript:alert(1.0)", 'https://a.example/x.jpg" onerror="alert(1)', "data:image/png;base64,AAAA"):
            self.assertNotIn("<img", html(kotu), kotu)

    def test_cok_yukselen_varsa_ilk_on_ikisi_kart_kalani_tablo(self):
        urunler = [Aday(f"Ürün {i:02d}", kaynaklar=UC_KAYNAK, son_satis=2000 + i, son_satis_gun=7, toplam_satis=20_000) for i in range(15)]
        html = sayfa(sirala(urunler, BUGUN), BUGUN)
        self.assertEqual(html.count('<div class="kart">'), 12)
        self.assertIn("<b>Diğer yükselenler</b> (3 ürün)", html)

    def test_karar_bolumu_yalnizca_bilgi_varsa(self):
        html = sayfa(sirala([Aday("Raf", kaynaklar=UC_KAYNAK, satis_sirasi=3)], BUGUN), BUGUN)
        self.assertNotIn("Türkiye, kâr ve karar", html)
        self.assertIn("<title>Yurt dışında çok satanlar ve yükselenler</title>", html)

    def test_listeden_gelen_metin_kod_olarak_calismaz(self):
        kotu = '<script>alert(1)</script><img src=x onerror=alert(1)>"\'>'
        aday = Aday(kotu, kategori=kotu, ulke=kotu, aciklama=kotu, orijinal_ad=kotu, marka=kotu, yurtdisi_fiyat=kotu,
                    urun_linkleri=["javascript:alert(2.0)", 'https://u.example/"><script>y</script>'],
                    satis_sirasi=2, tr_satici=1, maliyet=10.0, satis_fiyati=50.0,
                    kaynaklar=["javascript:alert(1.0)", "data:text/html,<b>x.y</b>", 'https://a.example/"><script>x</script>', "b.example/yol"])
        html = sayfa(sirala([aday], BUGUN), BUGUN, kotu, kotu)
        self.assertNotIn("<script", html.lower())
        self.assertNotIn("<img", html.lower())
        self.assertNotIn('href="javascript', html.lower())
        self.assertNotIn('href="data', html.lower())
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn('href="https://b.example/yol"', html)


class ExcelDosyasi(unittest.TestCase):
    def ac(self, veri, no):
        with zipfile.ZipFile(io.BytesIO(veri)) as z:
            return z.read(f"xl/worksheets/sheet{no}.xml").decode("utf-8")

    def test_dosya_gecerli_ve_yedi_sayfali(self):
        veri = dosya(sirala(oku(ORNEK), BUGUN), BUGUN)
        with zipfile.ZipFile(io.BytesIO(veri)) as z:
            self.assertIsNone(z.testzip())
            for ad in z.namelist():
                if ad.endswith(".xml") or ad.endswith(".rels"):
                    minidom.parseString(z.read(ad))
            kitap = z.read("xl/workbook.xml").decode("utf-8")
        for ad in ("Yükselenler", "Çok satanlar", "Çin'de tedarik", "Ürünleri incele", "Tüm ürünler", "Türkiye ve kâr", "Kaynaklar"):
            self.assertIn(f'name="{ad}"', kitap)
        self.assertIn('<f>IF(AND(ISNUMBER(D4),ISNUMBER(E4)),D4-E4-G4-H4,"")</f>', self.ac(veri, 6))

    def test_ilk_iki_sayfada_urun_baglantisi_adin_hemen_yaninda(self):
        veri = dosya(sirala(oku(ORNEK), BUGUN), BUGUN)
        yuk, cok = self.ac(veri, 1), self.ac(veri, 2)
        self.assertIn('<c r="C4" s="0" t="str"><f>HYPERLINK("https://ornek-videosatis.example/urun/slushy-cup","Ürünü aç")</f>', yuk)
        self.assertIn('"1688\'de ara")</f>', yuk)
        self.assertIn('<f>HYPERLINK("https://www.trendyol.com/sr?q=Buzlu+i%C3%A7ecek+barda%C4%9F%C4%B1","Trendyol\'da ara")</f>', yuk)
        self.assertIn("Frozen Slushy Squeeze Cup", yuk)
        self.assertIn('"Ürünü aç")</f>', cok)
        # ürün sayfası bilinmiyorsa görsel araması verilir
        tek = self.ac(dosya(sirala([Aday("Raf", kaynaklar=UC_KAYNAK, satis_sirasi=2)], BUGUN), BUGUN), 2)
        self.assertIn('<f>HYPERLINK("https://www.google.com/search?tbm=isch&amp;q=Raf","Görsellere bak")</f>', tek)

    def test_urunleri_incele_sayfasinda_tiklanabilir_baglantilar(self):
        incele = self.ac(dosya(sirala(oku(ORNEK), BUGUN), BUGUN), 4)
        for parca in ("Frozen Slushy Squeeze Cup", "$14.99", '<f>HYPERLINK("https://ornek-videosatis.example/urun/slushy-cup","Ürünü aç")</f>',
                      '<f>HYPERLINK("https://www.trendyol.com/sr?q=Buzlu+i%C3%A7ecek+barda%C4%9F%C4%B1","Trendyol")</f>',
                      "https://www.alibaba.com/trade/search?SearchText=Frozen+Slushy+Squeeze+Cup", "冰沙杯", "s.1688.com/selloffer/offer_search.htm?keywords=",
                      '<f>HYPERLINK("https://ornek-toptan.example/urun/slush","$1.35-1.80")</f>'):
            self.assertIn(parca, incele)

    def test_tirnakli_ya_da_zararli_urun_baglantisi_formule_girmez(self):
        aday = Aday("Raf", kaynaklar=UC_KAYNAK, satis_sirasi=2, orijinal_ad='Shelf",1)+CMD("x',
                    urun_linkleri=['https://a.example/x",A1)+HYPERLINK("http://kotu.example', "javascript:alert(1.0)"])
        incele = self.ac(dosya(sirala([aday], BUGUN), BUGUN), 4)
        self.assertNotIn("kotu.example&quot;,", incele.split("<f>")[1] if "<f>" in incele else "")
        for formul in incele.split("<f>")[1:]:
            self.assertNotIn("kotu.example", formul.split("</f>")[0])
            self.assertNotIn("CMD(", formul.split("</f>")[0])
            self.assertNotIn("javascript", formul.split("</f>")[0])

    def test_formul_gibi_gorunen_ad_calismaz(self):
        veri = dosya(sirala([Aday("=HYPERLINK(\"http://x\")", kaynaklar=UC_KAYNAK, satis_sirasi=2)], BUGUN), BUGUN)
        for no in (2, 4, 5, 6, 7):
            self.assertIn("'=HYPERLINK", self.ac(veri, no))
            self.assertNotIn("<f>HYPERLINK(&quot;http://x", self.ac(veri, no))

    def test_bos_satirda_formul_ve_varsayilanlar_durur(self):
        aday = Aday("Raf", kaynaklar=UC_KAYNAK, satis_sirasi=2, tr_satici=3, tr_fiyat=300.0, tr_kontrol="asistan",
                    tr_kaynaklar=["https://tr.example/ara"], aciklama="elle sayıldı")
        veri = dosya(sirala([aday], BUGUN, 18, 60), BUGUN, 18, 60)
        tr = self.ac(veri, 6)
        self.assertIn("IF(B4=0,", tr)
        self.assertIn("<v>0.18</v>", tr)
        self.assertIn("kaba sayıdır", tr)
        self.assertIn("tr.example/ara", self.ac(veri, 7))
        self.assertIn("elle sayıldı", self.ac(veri, 5))

    def test_bos_listeler_not_yazar(self):
        veri = dosya(sirala([Aday("Raf")], BUGUN), BUGUN)
        self.assertIn("yükselen sayılabilecek ürün çıkmadı", self.ac(veri, 1))
        self.assertIn("çok satan sayılabilecek ürün çıkmadı", self.ac(veri, 2))


    def test_cinde_tedarik_sayfasi_ture_gore_fiyat_ve_baglanti_verir(self):
        veri = dosya(sirala(oku(ORNEK), BUGUN), BUGUN)
        cin = self.ac(veri, 3)
        for parca in ("钛砧板", "$7.90-9.90", "$29.90", "1688'de ara", "Taobao'da ara", "Sayfayı aç", "bakılamadı", "liste fiyatıdır"):
            self.assertIn(parca, cin)
        bos = self.ac(dosya(sirala([Aday("Raf", kaynaklar=UC_KAYNAK, satis_sirasi=2)], BUGUN), BUGUN), 3)
        self.assertIn("toplanmadı", bos)


class CindeTedarik(unittest.TestCase):
    def test_ayni_turun_urunleri_tek_satirda_toplanir(self):
        ortak = dict(kategori="Hamile yastığı", cince_ad="孕妇枕", tedarik_fiyat="$4.25-18.99", tedarik_moq="20-1000", tedarikci="9 tedarikçi; Guangdong",
                     tedarik_linkleri=["https://www.made-in-china.example/multi-search/Pillow/F1/1.html"])
        sonuc = sirala([Aday("U yastık (A)", yurtdisi_fiyat="$39.99", **ortak), Aday("U yastık (B)", yurtdisi_fiyat="$24.89", **ortak),
                        Aday("Kuşak", kategori="Kuşak", cince_ad="托腹带"), Aday("Krem", kategori="Krem"),
                        Aday("Doğum çantası (dolu)", kategori="Hastane", cince_ad="待产包"), Aday("Lohusa yıkama şişesi (2'li)", kategori="Hastane", cince_ad="产妇冲洗瓶"),
                        Aday("Yıkama şişesi", kategori="Hastane", cince_ad="产妇冲洗瓶")], BUGUN)
        gruplar = tedarik_gruplari(sonuc)
        self.assertEqual([(g.tur, len(g.urunler), g.fiyat, g.yurtdisi) for g in gruplar],
                         [("Hamile yastığı", 2, "$4.25-18.99", "$24.89-39.99"), ("Yıkama şişesi", 2, "", ""), ("Doğum çantası", 1, "", ""),
                          ("Kuşak", 1, "", "")])
        self.assertEqual([e.split(" (")[0] for e, _ in gruplar[0].baglantilar], ["Tedarikçi sayfası", "1688", "Taobao"])
        self.assertEqual(tedarik_sayilari(sonuc), (2, 6))

    def test_tur_adi_urun_adlarinin_ortak_parcasidir(self):
        self.assertEqual(_ortak_ad(["Cepli hamile taytı", "Hamile taytı", "İspanyol paça hamile taytı"]), "Hamile taytı")
        self.assertEqual(_ortak_ad(["5'li telsiz emzirme sütyeni", "Eller serbest pompa ve emzirme sütyeni"]), "Emzirme sütyeni")
        self.assertEqual(_ortak_ad(["ızgara fırçası", "Tel ızgara fırçası"]), "Izgara fırçası")
        self.assertEqual(_ortak_ad(["Bide şişesi", "Lohusa duş şişesi"]), "")  # ortak tek kelime yetmez
        self.assertEqual(_ortak_ad(["Silikon yara izi jeli", "Silikon yara izi kremi"]), "")  # ortak baş sayılmaz
        self.assertEqual(_ortak_ad([]), "")

    def test_yurtdisi_fiyat_araligi_yalnizca_ayni_para_biriminde(self):
        self.assertEqual(_fiyat_araligi(["$24.89", "$35.99", ""]), "$24.89-35.99")
        self.assertEqual(_fiyat_araligi(["$9.99", "$9.99"]), "$9.99")
        self.assertEqual(_fiyat_araligi(["$9.99", "$12.50", "£6.45"]), "$9.99-12.50 · £6.45")
        self.assertEqual(_fiyat_araligi(["yaklaşık 10 dolar", "$25-$45", "$5"]), "$5")
        self.assertEqual(_fiyat_araligi([]), "")

    def test_rapor_sayfasinda_cinde_tedarik_bolumu(self):
        html = sayfa(sirala(oku(ORNEK), BUGUN), BUGUN, "Mutfak ürünleri")
        bolum = html.split("<h2>Çin&#x27;de tedarik</h2>" if "<h2>Çin&#x27;de tedarik</h2>" in html else "<h2>Çin'de tedarik</h2>")[1].split("<h2>")[0]
        for parca in ("钛砧板", "$7.90-9.90", "s.1688.com/selloffer", ">Taobao<", "bakılamadı", "nakliye, gümrük"):
            self.assertIn(parca, bolum)
        self.assertIn("üründe Çin fabrika fiyatı", html)
        bos = sayfa(sirala([Aday("Raf", kaynaklar=UC_KAYNAK, satis_sirasi=2)], BUGUN), BUGUN)
        self.assertIn("fabrika fiyatı ve Çince ürün adı toplanmadı", bos)

    def test_zararli_cince_ad_ve_tedarikci_kacislanir(self):
        aday = Aday("Raf", kaynaklar=UC_KAYNAK, satis_sirasi=2, cince_ad="<script>alert(1)</script>", tedarik_fiyat="<img src=x onerror=alert(1)>",
                    tedarikci="<b>x</b>", tedarik_linkleri=["javascript:alert(1)"])
        html = sayfa(sirala([aday], BUGUN), BUGUN)
        self.assertNotIn("<script", html.lower())
        self.assertNotIn("<img", html.lower())
        self.assertNotIn('href="javascript', html.lower())

    def test_komut_cin_tarafini_ve_eksigi_yazar(self):
        kod, metin, _ = main(["tara", str(ORNEK), "--tarih", "2026-10-12"])
        self.assertEqual(kod, 0)
        self.assertIn("ÇİN'DE TEDARİK — 12 ürünün 3 tanesinde fabrika liste fiyatı, 5 tanesinde Çince ad var", metin)
        self.assertIn("Eksik: öne çıkan", metin)


if __name__ == "__main__":
    unittest.main()
