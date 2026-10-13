"""Satış Bölge Analizcisi — komut satırı.

Sipariş listenizden satışlarınızın nereye gittiğini çıkarır: il, bölge, ilçe ve mahalle bazında;
sayılara dayanan bulgu ve önerileri yazar.

    python agent.py analiz siparisler.csv
    python agent.py analiz siparisler.csv --rapor rapor.html --excel sonuc.xlsx

Dosyada yalnızca il sütunu zorunludur; ilçe, mahalle, tutar, ürün, sipariş no ve durum isteğe bağlıdır.
Müşteri adı, telefon ve açık adres gerekmez; dosyada olsalar bile okunmaz.
Araç hiçbir siteye bağlanmaz. Ek paket gerekmez (Python 3.10+).
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

# Araç hangi klasörden ve hangi Python ayarıyla çalıştırılırsa çalıştırılsın kendi dosyalarını bulsun
# (bazı kum havuzları betiğin klasörünü arama yoluna eklemez).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from analiz import Rapor, Satir, analiz_et
from okuyucu import OkumaHatasi, oku
from rapor import UYARI, dosya
from rapor_html import sayfa


def tl(tutar: float) -> str:
    return f"{tutar:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def _yuzde(deger: float) -> str:
    return "%" + f"{deger:.1f}".replace(".", ",")


def _satir(x: Satir, r: Rapor, genislik: int) -> str:
    metin = f"  {x.ad:<{genislik}} {x.siparis:>6} sipariş  {_yuzde(x.pay):>6}"
    if x.ciro is not None:
        metin += f"   ciro {tl(x.ciro):>16}   ort. sepet {tl(x.ortalama_sepet):>12}"
    if r.iade_bilgisi_var and x.iade_orani is not None:
        metin += f"   iade {_yuzde(x.iade_orani):>6}"
    return metin


def yaz(r: Rapor) -> None:
    print(f"SATIŞ BÖLGE ANALİZİ — {r.siparis_sayisi} sipariş, {r.il_sayisi} il" + (f", ciro {tl(r.ciro)}" if r.ciro is not None else ""))
    print(f"  Siparişlerde ilk 3 ilin payı {_yuzde(r.ilk3_pay)}, ilk 10 ilin payı {_yuzde(r.ilk10_pay)}.")
    if r.iptal:
        print(f"  İptal edilen {r.iptal} satır analize girmedi.")
    print("\nBÖLGELER")
    for x in r.bolgeler:
        print(_satir(x, r, 20))
    print("\nEN ÇOK SİPARİŞ GELEN İLLER")
    for x in r.iller[:15]:
        print(_satir(x, r, 20))
    if len(r.iller) > 15:
        print(f"  … ve {len(r.iller) - 15} il daha (tamamı Excel dosyasında)")
    if r.ilceler:
        print("\nEN ÇOK SİPARİŞ GELEN İLÇELER")
        for x in r.ilceler[:10]:
            print(_satir(x, r, 30))
    for il in r.iller[:3]:
        ilceler = r.il_ilceleri.get(il.ad, [])
        if not ilceler:
            continue
        print(f"\n{il.ad.replace('i', 'İ').upper()} İÇİNDE İLÇELER" + (" VE MAHALLELER" if r.mahalle_bilgisi_var else ""))
        for x in ilceler[:6]:
            mahalleler = r.ilce_mahalleleri.get(f"{il.ad} / {x.ad}", [])
            ek = ("   mahalleler: " + ", ".join(f"{m.ad} {m.siparis}" for m in mahalleler[:4])) if mahalleler else ""
            print(f"  {x.ad:<20} {x.siparis:>6} sipariş  ildeki payı {_yuzde(100 * x.siparis / il.siparis):>6}{ek}")
    if r.mahalleler:
        print("\nEN ÇOK SİPARİŞ GELEN MAHALLELER")
        for x in r.mahalleler[:10]:
            print(f"  {x.ad:<44} {x.siparis:>6} sipariş")
    if r.urun_bilgisi_var:
        print("\nİLK 5 İLDE EN ÇOK SATAN ÜRÜN")
        for x in r.iller[:5]:
            print(f"  {x.ad:<20} {x.en_cok_satan}")
    if r.siparis_gelmeyen_iller:
        print(f"\nSİPARİŞ GELMEYEN İLLER ({len(r.siparis_gelmeyen_iller)})")
        print("  " + ", ".join(r.siparis_gelmeyen_iller))
    print(f"\nBULGULAR VE ÖNERİLER ({len(r.oneriler)})")
    for no, o in enumerate(r.oneriler, 1):
        print(f"  {no}. [{o.tur}] {o.baslik}\n     Bulgu: {o.bulgu}\n     Öneri: {o.oneri}")
    if not r.oneriler:
        print("  Bu listede kural eşiklerini aşan bir bulgu çıkmadı.")
    for u in r.uyarilar:
        print(f"\nNot: {u}")
    print(f"\n{UYARI}")


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
    p = argparse.ArgumentParser(description="Sipariş listesinden il, bölge, ilçe ve mahalle bazında satış dağılımı, bulgular ve öneriler.")
    alt = p.add_subparsers(dest="komut", required=True)
    q = alt.add_parser("analiz", help="Sipariş listesini analiz eder")
    q.add_argument("dosya", help="Sipariş listesi (.csv); zorunlu sütun: il")
    q.add_argument("--excel", metavar="DOSYA", help="Sonucu Excel dosyası olarak da kaydeder, ör. sonuc.xlsx")
    q.add_argument("--rapor", metavar="DOSYA", help="Rapor sayfasını (HTML) kaydeder, ör. rapor.html")
    q.add_argument("--baslik", default="", help="Rapor sayfasının başlığı, ör. \"Mağazam: Temmuz-Eylül satış bölge raporu\"")
    q.add_argument("--tarih", metavar="YYYY-AA-GG", help="Rapor tarihi; verilmezse bugün")
    a = p.parse_args(argv)
    try:
        siparisler = oku(a.dosya)
        r = analiz_et(siparisler)
    except (OkumaHatasi, ValueError) as hata:
        print(f"Hata: {hata}", file=sys.stderr)
        return 1
    try:
        bugun = date.fromisoformat(a.tarih) if a.tarih else date.today()
    except ValueError:
        print("Hata: --tarih YYYY-AA-GG biçiminde olmalı, ör. 2026-10-13", file=sys.stderr)
        return 1
    yaz(r)
    if a.rapor:
        yol = Path(a.rapor).expanduser()
        if yol.suffix.lower() not in (".html", ".htm"):
            yol = yol.with_suffix(".html")
        try:
            yol.write_text(sayfa(r, bugun, a.baslik), encoding="utf-8")
        except OSError as hata:
            print(f"Hata: rapor sayfası yazılamadı: {hata}", file=sys.stderr)
            return 1
        print(f"\nRapor sayfası kaydedildi: {yol}")
    if a.excel:
        yol = Path(a.excel).expanduser()
        if yol.suffix.lower() != ".xlsx":
            yol = yol.with_suffix(".xlsx")
        try:
            yol.write_bytes(dosya(siparisler, r))
        except OSError as hata:
            print(f"Hata: Excel dosyası yazılamadı: {hata}", file=sys.stderr)
            return 1
        print(f"\nExcel dosyası kaydedildi: {yol}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
