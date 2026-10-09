"""Ürün, Fiyat ve Rakip Analizcisi — komut satırı.

Bir ürün listesinden (CSV) üç hesap yapar:

    python agent.py ortalama liste.csv            pazarın ortalama fiyatı, puanı, yorum ve favori sayıları
    python agent.py konum liste.csv 349,90        bu fiyatın pazardaki yeri
    python agent.py rakip liste.csv               listede "benim" diye işaretli ürünün rakiplerle karşılaştırması
    python agent.py hepsi liste.csv               verilen listeyle yapılabilen hesapların tümü

Her komuta --excel sonuc.xlsx eklenirse sonuç Excel dosyası olarak da kaydedilir.
Araç hiçbir siteye bağlanmaz; listeyi siz hazırlarsınız. Ek paket gerekmez (Python 3.10+).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analiz import Konum, Olcu, Ozet, RakipRaporu, ayir, konum, ozet, rakip_karsilastir, tl
from okuyucu import OkumaHatasi, oku, sayi
from rapor import UYARI, dosya


def _sayi(deger: float | None, basamak: int = 0) -> str:
    if deger is None:
        return "bilinmiyor"
    return f"{deger:,.{basamak}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _satir(etiket: str, deger: str) -> str:
    return f"  {etiket:<34} {deger}"


def ozet_yaz(o: Ozet) -> None:
    def olcu(x: Olcu, basamak: int = 0) -> str:
        return f"ortalama {_sayi(x.ortalama, basamak)}, ortanca {_sayi(x.ortanca, basamak)} ({x.adet} ürün)" if x.adet else "veri yok"

    print(f"ÜRÜN ORTALAMALARI — {o.urun_sayisi} ürün")
    print(_satir("Ortalama fiyat", tl(o.fiyat.ortalama)))
    print(_satir("Ortanca fiyat", tl(o.fiyat.ortanca)))
    print(_satir("En düşük – en yüksek fiyat", f"{tl(o.fiyat.en_az)} – {tl(o.fiyat.en_cok)}"))
    print(_satir("Ürünlerin ortadaki yarısı", f"{tl(o.alt_ceyrek)} – {tl(o.ust_ceyrek)}"))
    if o.yorum_agirlikli_fiyat is not None:
        print(_satir("Yorum ağırlıklı ortalama fiyat", tl(o.yorum_agirlikli_fiyat)))
    print(_satir("Puan", olcu(o.puan, 1)))
    print(_satir("Yorum sayısı", olcu(o.yorum)))
    print(_satir("Favori sayısı", olcu(o.favori)))
    if o.ucretsiz_kargo_orani is not None:
        print(_satir("Ücretsiz kargolu ürün oranı", f"%{_sayi(o.ucretsiz_kargo_orani)} ({o.kargo_bilinen} ürün)"))
    for u in o.uyarilar:
        print(f"  Not: {u}")


def konum_yaz(k: Konum) -> None:
    print(f"FİYAT KONUMU — {tl(k.fiyat)}")
    print(_satir("Karşılaştırılan ürün", str(k.urun_sayisi)))
    print(_satir("Sizden ucuz / aynı / pahalı", f"{k.daha_ucuz} / {k.ayni} / {k.daha_pahali}"))
    print(_satir("Pazardaki yeriniz", f"{k.dilim} (0–100 ölçeğinde {_sayi(k.yuzdelik)}; 0 en ucuz)"))
    yon = "ucuz" if k.ortancadan_fark < 0 else "pahalı"
    fark = f"ortancadan %{_sayi(abs(k.ortancadan_fark), 1)} {yon}" if k.ortancadan_fark else "ortancayla aynı"
    print(_satir("Pazarın ortanca fiyatı", f"{tl(k.ortanca)} ({fark})"))
    print(_satir("Ana fiyat aralığı", f"{tl(k.ana_aralik[0])} – {tl(k.ana_aralik[1])} "
                                      f"({'içindesiniz' if k.ana_aralikta else 'dışındasınız'})"))
    yakin = f"{k.yakin_sayisi} ürün"
    if k.yakin_sayisi:
        yakin += f"; ortanca puan {_sayi(k.yakin_ortanca_puan, 1)}, ortanca yorum {_sayi(k.yakin_ortanca_yorum)}"
    print(_satir("Benzer fiyatlı ürünler (±%10)", yakin))
    print("  Fiyat dilimleri (ürünler dört eşit gruba bölünür):")
    for i, d in enumerate(k.dilimler, 1):
        isaret = "  ← en çok ilgi gören" if k.ilgi_goren is d else ""
        print(f"    {i}. {tl(d.alt)} – {tl(d.ust)}: {d.urun_sayisi} ürün, ortanca yorum {_sayi(d.ortanca_yorum)}{isaret}")
    for u in k.uyarilar:
        print(f"  Not: {u}")


def rakip_yaz(r: RakipRaporu) -> None:
    print(f"RAKİP KARŞILAŞTIRMASI — {r.benim.ad} ({r.rakip_sayisi} rakip)")
    for k in r.kiyaslar:
        if k.olcu == "Kargo":
            print(_satir(k.olcu, f"siz: {k.benim} | rakipler: {k.rakip_ortancasi} | {k.durum}"))
            continue
        print(_satir(k.olcu, f"siz: {k.benim} | rakip ortancası: {k.rakip_ortancasi} | {k.durum}"))
        print(f"  {'':<34} {k.aciklama}")
    print(_satir("Öne geçtiğiniz noktalar", ", ".join(r.onde) if r.onde else "yok"))
    print(_satir("Geride kaldığınız noktalar", ", ".join(r.geride) if r.geride else "yok"))
    for u in r.uyarilar:
        print(f"  Not: {u}")


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


def main(argv: list[str] | None = None) -> int:
    cikti_kodlamasini_ayarla()
    p = argparse.ArgumentParser(description="Ürün ortalamaları, fiyat konumu ve rakip karşılaştırması.")
    alt = p.add_subparsers(dest="komut", required=True)
    for ad, yardim in (("ortalama", "Pazarın ortalama fiyatı, puanı, yorum ve favori sayıları"),
                       ("konum", "Bir fiyatın pazardaki yeri"),
                       ("rakip", "Listede 'benim' diye işaretli ürünün rakiplerle karşılaştırması"),
                       ("hepsi", "Verilen listeyle yapılabilen hesapların tümü")):
        q = alt.add_parser(ad, help=yardim)
        q.add_argument("dosya", help="Ürün listesi (.csv)")
        if ad == "konum":
            q.add_argument("fiyat", nargs="?", help="Sizin fiyatınız (TL); verilmezse listede 'benim' diye işaretli ürünün fiyatı kullanılır")
        if ad == "hepsi":
            q.add_argument("--fiyat", help="Sizin fiyatınız (TL); verilmezse listede 'benim' diye işaretli ürünün fiyatı kullanılır")
        q.add_argument("--excel", metavar="DOSYA", help="Sonucu Excel dosyası olarak da kaydeder, ör. sonuc.xlsx")
    a = p.parse_args(argv)

    try:
        benim, pazar = ayir(oku(a.dosya))
        fiyat = None
        verilen = getattr(a, "fiyat", None)
        if verilen is not None:
            fiyat = sayi(verilen)
            if fiyat is None or fiyat <= 0:
                raise ValueError(f"Fiyat anlaşılamadı: {verilen!r}. Sayı olmalı, ör. 899 veya 1.299,90")
        elif benim is not None:
            fiyat = benim.fiyat
        if a.komut == "konum" and fiyat is None:
            raise ValueError("Fiyat verilmedi. Komuta fiyatınızı ekleyin ya da listede kendi ürününüzü 'benim' sütununda işaretleyin")

        o = ozet(pazar)
        k = konum(pazar, fiyat) if fiyat is not None and a.komut in ("konum", "hepsi") else None
        r = None
        if a.komut == "rakip" or (a.komut == "hepsi" and benim is not None):
            r = rakip_karsilastir(benim, pazar)
        # Excel dosyasına, verilen listeyle hesaplanabilen bölümlerin hepsi girsin.
        k_dosya = k or (konum(pazar, fiyat) if fiyat is not None else None)
        r_dosya = r or (rakip_karsilastir(benim, pazar) if benim is not None else None)
    except (OkumaHatasi, ValueError) as hata:
        print(f"Hata: {hata}", file=sys.stderr)
        return 1

    bolumler = []
    if a.komut in ("ortalama", "hepsi"):
        bolumler.append(lambda: ozet_yaz(o))
    if k:
        bolumler.append(lambda: konum_yaz(k))
    if r:
        bolumler.append(lambda: rakip_yaz(r))
    for i, yaz in enumerate(bolumler):
        if i:
            print()
        yaz()
    if a.komut == "hepsi" and benim is None:
        print("\nRakip karşılaştırması yapılmadı: listede 'benim' diye işaretli ürün yok."
              + ("" if fiyat is not None else " Fiyat konumu için de fiyat verilmedi."))
    print(f"\n{UYARI}")

    if a.excel:
        yol = Path(a.excel).expanduser()
        if yol.suffix.lower() != ".xlsx":
            yol = yol.with_suffix(".xlsx")
        try:
            yol.write_bytes(dosya(pazar, o, k_dosya, r_dosya))
        except OSError as hata:
            print(f"Hata: Excel dosyası yazılamadı: {hata}", file=sys.stderr)
            return 1
        print(f"\nExcel dosyası kaydedildi: {yol}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
