"""Ürün Araştırma Agent'ı — komut satırı.

Yurt dışında çok satan ve yükselen ürünlerin listesini (CSV) puanlar; rapor sayfası ve Excel üretir:

    python agent.py tara urunler.csv --alan "Mutfak ürünleri" --rapor rapor.html --excel rapor.xlsx
    python agent.py tara urunler.csv --komisyon 18 --kargo 60

Listede Türkiye'deki ilan sayısı, maliyet ve satış fiyatı da varsa rekabet, kâr ve karar eklenir.
--komisyon ve --kargo, listede bu sütunları boş olan ürünler için kullanılır.
Araç hiçbir siteye bağlanmaz; ürün listesini asistan ya da siz hazırlarsınız. Ek paket gerekmez (Python 3.10+).
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

# Araç hangi klasörden ve hangi Python ayarıyla çalıştırılırsa çalıştırılsın kendi dosyalarını bulsun
# (bazı kum havuzları betiğin klasörünü arama yoluna eklemez).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from analiz import (RISK_ETIKETI, Degerlendirme, Puan, adaylar, adet_yaz, alan_adi, aylik_satis, bilgi_girilenler, cok_satanlar, derinlesti,
                    digerleri, guncel_ozet, iki_listede, inceleme_baglantilari, kaynak_ciftleri, sirala, tedarik_gruplari, tedarik_sayilari, tl,
                    yukselenler, yuzde_yaz)
from okuyucu import OkumaHatasi, oku, sayi, tarih
from rapor import UYARI, dosya
from rapor_html import sayfa, tarih_yaz


def _satir(etiket: str, deger: str) -> str:
    return f"   {etiket:<15} {deger}"


def _kisa(ad: str, n: int = 44) -> str:
    return ad if len(ad) <= n else ad[:n - 1] + "…"


def _p(p: Puan) -> str:
    return "-" if p.puan is None else str(p.puan)


def _puan_satiri(p: Puan) -> str:
    if p.puan is None:
        return "ölçülemedi (hiçbir işareti görülmedi)"
    return f"{p.puan}/100, kanıt {p.kanit} (" + ", ".join(f"{ad} {alinan}/{tavan}" for ad, (alinan, tavan) in p.parcalar.items()) + ")"


LISTE_BOYU = 30  # konsolda her listenin ilk bu kadar satırı yazılır; tamamı rapor ve Excel dosyasındadır


def _devami(toplam: int, gosterilen: int = LISTE_BOYU) -> None:
    if toplam > gosterilen:
        print(f"      … ve {toplam - gosterilen} ürün daha (tamamı rapor sayfasında ve Excel'de)")


def listeleri_yaz(sonuc: list[Degerlendirme], bugun: date) -> None:
    yuk, cok, ady, dig = yukselenler(sonuc), cok_satanlar(sonuc), adaylar(sonuc), digerleri(sonuc)
    print(f"YÜKSELENLER — {len(yuk)} ürün (yükselişi satış rakamıyla ölçülenler)")
    if yuk:
        print(f"  {'#':>2}  {'Ürün':<44} {'Yükseliş':>8} {'Kanıt':<7} {'Satış gücü':>10}  Sınıf")
        for i, d in enumerate(yuk[:LISTE_BOYU], 1):
            print(f"  {i:>2}  {_kisa(d.aday.ad):<44} {_p(d.yukselis):>8} {d.yukselis.kanit:<7} {_p(d.satis):>10}  {d.sinif}")
        _devami(len(yuk))
    else:
        print("  Bu taramada yükselişi satış rakamıyla ölçülebilen ürün çıkmadı.")
    ortak = iki_listede(sonuc)
    print(f"\nÇOK SATANLAR — {len(cok)} ürün" + (f" ({ortak} tanesi yükselenler listesinde de var)" if ortak else ""))
    if cok:
        print(f"  {'#':>2}  {'Ürün':<44} {'Satış gücü':>10} {'Sıra':>6} {'30 gün satış':>13} {'Toplam satış':>13} {'Yorum':>9} {'Yükseliş':>8}")
        for i, d in enumerate(cok[:LISTE_BOYU], 1):
            a, aylik = d.aday, aylik_satis(d.aday)
            print(f"  {i:>2}  {_kisa(a.ad):<44} {_p(d.satis):>10} {adet_yaz(a.satis_sirasi) if a.satis_sirasi else '-':>6} "
                  f"{adet_yaz(aylik) if aylik is not None else '-':>13} {adet_yaz(a.toplam_satis) if a.toplam_satis is not None else '-':>13} "
                  f"{adet_yaz(a.yorum) if a.yorum is not None else '-':>9} {_p(d.yukselis):>8}")
        _devami(len(cok))
    else:
        print("  Bu taramada çok satan sayılabilecek ürün çıkmadı.")
    if ady:
        print(f"\nYAZILARDA GEÇENLER — {len(ady)} ürün (izleme listesi: satış rakamı görülemedi, yükselişi doğrulanmadı)")
        for d in ady[:LISTE_BOYU]:
            n, son = guncel_ozet(d.aday, bugun)
            nerede = "; ".join(([f"{n} sitede güncel yazı, en yenisi {tarih_yaz(son)}"] if n else [])
                               + (["arama ilgisi yükseliyor"] if d.aday.trend == "yükseliyor" else []))
            print(f"   {_kisa(d.aday.ad)} — {nerede}")
        _devami(len(ady))
    if dig:
        print(f"\nÖNE ÇIKMAYANLAR — {len(dig)} ürün")
        for d in dig[:10]:
            print(f"   {_kisa(d.aday.ad)} — {d.sinif}: {d.sinif_gerekce}")
        _devami(len(dig), 10)


def tedarik_yaz(sonuc: list[Degerlendirme]) -> None:
    fiyatli, cinceli = tedarik_sayilari(sonuc)
    print(f"\nÇİN'DE TEDARİK — {len(sonuc)} ürünün {fiyatli} tanesinde fabrika liste fiyatı, {cinceli} tanesinde Çince ad var")
    gruplar = tedarik_gruplari(sonuc)
    if gruplar:
        print(f"  {'Ürün türü':<34} {'Çince adı':<12} {'Yurt dışı':<16} {'Çin fabrika (liste)':<20} {'En az sipariş':<14} Ürün")
        for g in gruplar[:LISTE_BOYU]:
            print(f"  {_kisa(g.tur, 34):<34} {g.cince_ad or '-':<12} {g.yurtdisi or '-':<16} {g.fiyat or 'bakılamadı':<20} {g.moq or '-':<14} "
                  f"{len(g.urunler)}")
        _devami(len(gruplar))
        print("  Liste fiyatıdır: nakliye, gümrük, vergi ve pazarlık dahil değildir; kâr hesabında kullanılmaz.")
    one_cikan = yukselenler(sonuc) + [d for d in cok_satanlar(sonuc) if d not in yukselenler(sonuc)]
    eksik = [d.aday.ad for d in one_cikan if not d.aday.tedarik_fiyat.strip()]
    if eksik:
        print(f"  Eksik: öne çıkan {len(one_cikan)} ürünün {len(eksik)} tanesinde Çin fabrika fiyatı yok "
              f"(bakılmadıysa SKILL.md'deki F adımını bu ürün türleri için tamamlayın): {', '.join(_kisa(x, 40) for x in eksik[:8])}"
              + (" …" if len(eksik) > 8 else ""))


def karar_tablosu_yaz(sonuc: list[Degerlendirme]) -> None:
    girilen = bilgi_girilenler(sonuc)
    print(f"\nTÜRKİYE, KÂR VE KARAR — {len(girilen)} ürün")
    print(f"  {'Ürün':<44} {'Türkiye':<11} {'Kâr/ürün':>12} {'Marj':>7}  Karar")
    for d in girilen:
        print(f"  {_kisa(d.aday.ad):<44} {d.rekabet:<11} {tl(d.kar.net) if d.kar else '-':>12} "
              f"{yuzde_yaz(d.kar.marj) if d.kar else '-':>7}  {d.karar}")
    if len(girilen) < len(sonuc):
        print(f"  Diğer {len(sonuc) - len(girilen)} ürün için Türkiye ve maliyet bilgisi girilmedi; karar yazılmadı.")


def ayrinti_yaz(i: int, d: Degerlendirme, karar_goster: bool) -> None:
    a = d.aday
    print(f"{i}. {a.ad} — {d.sinif}")
    kimlik = " · ".join(x for x in (a.orijinal_ad, a.cince_ad, a.marka, a.yurtdisi_fiyat,
                                     f"Çin'de tedarik {a.tedarik_fiyat}" if a.tedarik_fiyat else "") if x)
    if kimlik:
        print(_satir("Listedeki adı", kimlik))
    print(_satir("Neden", d.sinif_gerekce))
    print(_satir("Yükseliş", _puan_satiri(d.yukselis)))
    print(_satir("Satış gücü", _puan_satiri(d.satis)))
    for j, r in enumerate(d.yukselis.aciklamalar + d.satis.aciklamalar + ([f"Video izlenmesi: {adet_yaz(a.izlenme)}."] if a.izlenme else [])):
        print(_satir("Rakamlar" if j == 0 else "", r))
    eksik = d.yukselis.eksikler + d.satis.eksikler
    if eksik:
        print(_satir("Görülemeyen", ", ".join(eksik)))
    if a.ulke or a.veri_tarihi:
        print(_satir("Veri", " · ".join(x for x in (a.ulke, tarih_yaz(a.veri_tarihi) if a.veri_tarihi else "") if x)))
    if karar_goster:
        print(_satir("Türkiye", d.rekabet_aciklama + (f" Görülen fiyat: {tl(a.tr_fiyat)}." if a.tr_fiyat else "")))
        if d.kar:
            k = d.kar
            komisyon = f"komisyon {tl(k.komisyon_tutari)} ({yuzde_yaz(k.komisyon_orani)})" if k.komisyon_orani is not None else "komisyon girilmedi"
            kargo = f"kargo {tl(k.kargo)}" if "kargo" not in k.eksikler else "kargo girilmedi"
            print(_satir("Kâr", f"ürün başına {tl(k.net)}, marj {yuzde_yaz(k.marj)}"))
            print(_satir("", f"{k.fiyat_kaynagi} {tl(k.fiyat)} − maliyet {tl(k.maliyet)} − {komisyon} − {kargo}"))
        else:
            yok = [ad for ad, deger in (("maliyet", a.maliyet), ("satış fiyatı", a.satis_fiyati if a.satis_fiyati is not None else a.tr_fiyat))
                   if deger is None]
            print(_satir("Kâr", f"hesaplanamadı ({' ve '.join(yok)} girilmedi)"))
        if d in bilgi_girilenler([d]):
            print(_satir("Karar", f"{d.karar}. {d.gerekce}"))
    if d.riskler:
        for j, r in enumerate(d.riskler):
            print(_satir("Risk" if j == 0 else "", f"[{RISK_ETIKETI[r.duzey]}] {r.mesaj}"))
    else:
        print(_satir("Risk", "uyarı çıkmadı (ürünün serbest olduğunu göstermez)"))
    kaynaklar = [k + (f" (yayın: {tarih_yaz(t)})" if t else "") for k, t in kaynak_ciftleri(a)]
    for j, k in enumerate(kaynaklar or ["kaynak bağlantısı yok"]):
        print(_satir("Kaynak" if j == 0 else "", k))
    for grup, baglantilar in inceleme_baglantilari(a).items():
        for j, (etiket, adres) in enumerate(baglantilar):
            print(_satir(grup if j == 0 else "", f"{etiket}: {adres}"))
    if a.tr_kaynaklar:
        print(_satir("Türkiye'de bakılan", " ".join(a.tr_kaynaklar)))
    if a.aciklama:
        print(_satir("Listedeki not", a.aciklama))


def cikti_kodlamasini_ayarla() -> None:
    """Türkçe harfleri gösteremeyen bir ortamda (ör. ASCII'ye ayarlı bir kum havuzu) çıktı yazarken çökmeyi önler."""
    for akis in (sys.stdout, sys.stderr):
        ayarla = getattr(akis, "reconfigure", None)
        if ayarla is None:
            continue
        if (getattr(akis, "encoding", None) or "").lower().replace("_", "-") in ("ascii", "us-ascii", "ansi-x3.4-1968", "646"):
            ayarla(encoding="utf-8", errors="replace")
        else:
            ayarla(errors="replace")


def _oran(metin: str | None, ad: str, ust: float | None = None) -> float | None:
    if metin is None:
        return None
    deger = sayi(metin)
    if deger is None or deger < 0 or (ust is not None and deger >= ust):
        raise ValueError(f"{ad} anlaşılamadı: {metin!r}. Sayı olmalı, ör. 18 ya da 18,5")
    return deger


def _yaz(yol_metni: str, uzanti: str, icerik: bytes, ad: str) -> bool:
    yol = Path(yol_metni).expanduser()
    if yol.suffix.lower() != uzanti:
        yol = yol.with_suffix(uzanti)
    try:
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_bytes(icerik)
    except OSError as hata:
        print(f"Hata: {ad} yazılamadı: {hata}", file=sys.stderr)
        return False
    print(f"{ad} kaydedildi: {yol}")
    return True


def main(argv: list[str] | None = None) -> int:
    cikti_kodlamasini_ayarla()
    p = argparse.ArgumentParser(description="Yurt dışında çok satan ve yükselen ürünlerin listesini puanlar; rapor ve Excel üretir.")
    alt = p.add_subparsers(dest="komut", required=True)
    for komut, yardim in (("tara", "Ürün listesini satış gücü ve yükselişe göre puanlar, raporu üretir"),
                          ("degerlendir", "tara ile aynıdır; listede Türkiye ve maliyet bilgisi varsa rekabet, kâr ve karar eklenir")):
        q = alt.add_parser(komut, help=yardim)
        q.add_argument("dosya", help="Ürün listesi (.csv)")
        q.add_argument("--alan", default="", help='Raporun başlığına yazılacak alan, ör. "Mutfak ürünleri"')
        q.add_argument("--tarih", help="Rapor tarihi (YYYY-AA-GG); verilmezse bugün. Kaynakların güncelliği bu tarihe göre ölçülür")
        q.add_argument("--komisyon", help="Listede komisyonu boş olan ürünler için pazaryeri komisyonu (yüzde), ör. 18")
        q.add_argument("--kargo", help="Listede kargosu boş olan ürünler için müşteriye gönderim masrafı (TL), ör. 60")
        q.add_argument("--rapor", metavar="DOSYA", help="Rapor sayfasını kaydeder, ör. rapor.html")
        q.add_argument("--excel", metavar="DOSYA", help="Sonucu Excel dosyası olarak da kaydeder, ör. rapor.xlsx")
        q.add_argument("--acilmayan", default="", help="Taramada engellendiği için açılamayan siteler; raporun sınırlar bölümüne yazılır")
        q.add_argument("--ayrinti", action="store_true", help="Bütün ürünlerin ayrıntısını yazar (verilmezse yalnızca öne çıkanlar)")
    a = p.parse_args(argv)

    try:
        komisyon = _oran(a.komisyon, "Komisyon", 100)
        kargo = _oran(a.kargo, "Kargo")
        bugun = date.today()
        if a.tarih:
            bugun = tarih(a.tarih)
            if bugun is None:
                raise ValueError(f"Tarih anlaşılamadı: {a.tarih!r}. Örnek: 2026-10-12")
        sonuc = sirala(oku(a.dosya), bugun, komisyon, kargo)
    except (OkumaHatasi, ValueError) as hata:
        print(f"Hata: {hata}", file=sys.stderr)
        return 1

    siteler = {alan_adi(k) for d in sonuc for k in d.aday.kaynaklar if alan_adi(k)}
    print("ÜRÜN ARAŞTIRMA RAPORU" + (f" — {a.alan.strip()}" if a.alan.strip() else "")
          + f" — {tarih_yaz(bugun)} — {len(sonuc)} ürün, {len(siteler)} kaynak site\n")
    kaynaksiz = [d.aday.ad for d in sonuc if not d.kaynak_sayisi]
    if kaynaksiz:
        adlar = ", ".join(kaynaksiz[:5]) + (" …" if len(kaynaksiz) > 5 else "")
        print(f"Not: {len(kaynaksiz)} üründe kaynak bağlantısı yok; rakamları doğrulanamadığı için 'Kanıt yetersiz' sayıldı: {adlar}\n")
    donemsiz = [d.aday.ad for d in sonuc if d.aday.son_satis is not None and not d.aday.son_satis_gun]
    if donemsiz:
        print(f"Not: {len(donemsiz)} üründe satış adedinin kaç güne ait olduğu (son_satis_gun) yazılmamış; "
              f"bu adetler puana girmedi: {', '.join(donemsiz[:5])}\n")
    gelecek = [d.aday.ad for d in sonuc if any(t is not None and t > bugun for t in d.aday.kaynak_tarihleri)]
    if gelecek:
        print(f"Not: {len(gelecek)} üründe rapor tarihinden sonraya ait kaynak tarihi var; bu tarihler sayılmadı: {', '.join(gelecek[:5])}\n")
    if a.acilmayan.strip():
        print(f"Not: Bu taramada açılamayan kaynaklar: {a.acilmayan.strip()}\n")
    karar_goster = derinlesti(sonuc)
    if karar_goster and (komisyon is not None or kargo is not None):
        parcalar = ([f"komisyon {yuzde_yaz(komisyon)}"] if komisyon is not None else []) + ([f"kargo {tl(kargo)}"] if kargo is not None else [])
        print(f"Not: Listede boş bırakılan ürünlerde {' ve '.join(parcalar)} kullanıldı.\n")

    listeleri_yaz(sonuc, bugun)
    tedarik_yaz(sonuc)
    if karar_goster:
        karar_tablosu_yaz(sonuc)
    else:
        print("\nTürkiye'deki rekabet, kâr ve karar hesaplanmadı: listede Türkiye'deki ilan sayısı ya da maliyet yok. "
              "Satıcı bu rakamları verince aynı komut bunları da ekler.")
    yuk = yukselenler(sonuc)
    one_cikan = yuk[:15] + [d for d in cok_satanlar(sonuc) if d not in yuk][:10] + [d for d in bilgi_girilenler(sonuc)]
    gosterilecek = sonuc if a.ayrinti else [d for d in sonuc if d in one_cikan]
    print("\nAYRINTI" + ("" if a.ayrinti or len(gosterilecek) == len(sonuc)
                          else f" — öne çıkan {len(gosterilecek)} ürün (hepsi rapor ve Excel dosyasında; burada görmek için --ayrinti)"))
    for i, d in enumerate(gosterilecek, 1):
        print()
        ayrinti_yaz(i, d, karar_goster)
    print(f"\n{UYARI}\n")

    tamam = True
    if a.rapor:
        tamam &= _yaz(a.rapor, ".html", sayfa(sonuc, bugun, a.alan, a.acilmayan).encode("utf-8"), "Rapor sayfası")
    if a.excel:
        tamam &= _yaz(a.excel, ".xlsx", dosya(sonuc, bugun, komisyon, kargo), "Excel dosyası")
    return 0 if tamam else 1


if __name__ == "__main__":
    sys.exit(main())
