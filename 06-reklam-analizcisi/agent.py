"""Reklam Analizcisi — komut satırı.

Pazaryerinin ya da reklam panelinin indirdiğiniz reklam raporundan hangi reklamın satış getirdiğini, hangisinin
bütçeyi boşa harcadığını çıkarır; maliyet bilgisi verirseniz reklamdan sonra elinize ne kaldığını hesaplar.

    python agent.py sutunlar reklam_raporu.xlsx
    python agent.py analiz reklam_raporu.xlsx
    python agent.py analiz reklam_raporu.csv --maliyet maliyetler.csv --rapor rapor.html --excel sonuc.xlsx
    python agent.py analiz reklam_raporu.csv --kar-marji 25
    python agent.py analiz reklam_raporu.csv --sutun harcama="Harcanan Tutar" --sutun ciro="Reklam Satışı"

Rapor .csv ya da .xlsx olabilir. Zorunlu: harcama sütunu ve ürün, kampanya ya da arama terimi sütunlarından biri.
Araç hiçbir siteye bağlanmaz ve reklam hesabında değişiklik yapmaz. Ek paket gerekmez (Python 3.10+).
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analiz import Kalem, Rapor, analiz_et
from okuyucu import ALAN_ADLARI, OkumaHatasi, maliyet_oku, oku, sutunlari_goster
from rapor import UYARI, dosya
from rapor_html import sayfa


def tl(x: float | None) -> str:
    return "—" if x is None else f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def yz(x: float | None) -> str:
    return "—" if x is None else "%" + f"{x:.1f}".replace(".", ",")


def sy(x: float | None) -> str:
    return "—" if x is None else f"{x:,.0f}".replace(",", ".")


def kat(x: float | None) -> str:
    return "—" if x is None else f"{x:.2f}".replace(".", ",")


def _satir(k: Kalem, genislik: int, kar: bool) -> str:
    ad = k.ad if len(k.ad) <= genislik else k.ad[: genislik - 1] + "…"
    metin = (f"  {ad:<{genislik}} harcama {tl(k.harcama):>14}  satış {tl(k.ciro):>14}  ROAS {kat(k.roas):>6}  "
             f"maliyet oranı {yz(k.acos):>7}  sipariş {sy(k.siparis):>5}  tıklama {sy(k.tiklama):>6}")
    if kar:
        metin += f"  başa baş {yz(k.basa_bas_acos):>7}  reklam sonrası {tl(k.net):>14}"
    return metin + (f"  [{k.durum}]" if k.durum else "")


def yaz(r: Rapor) -> None:
    print(f"REKLAM ANALİZİ — {r.satir_sayisi} satır, {len(r.kalemler)} {r.birim.lower()}"
          + (f", {len(r.terimler)} arama terimi" if r.terimler else ""))
    print(f"  Harcama {tl(r.harcama)} · reklamdan gelen satış {tl(r.ciro)} · ROAS {kat(r.roas)} · reklam maliyet oranı {yz(r.acos)}")
    print(f"  Sipariş {sy(r.siparis)} · tıklama {sy(r.tiklama)} · gösterim {sy(r.gosterim)} · tıklama oranı {yz(r.ctr)} · "
          f"dönüşüm {yz(r.cvr)} · tıklama başı {tl(r.tbm)}")
    print(f"  Satış getirmeyen harcama: {tl(r.satis_getirmeyen_harcama)}")
    if r.maliyet_var:
        print(f"  Reklam sonrası kalan (maliyeti bilinen kalemler): {tl(r.net)}")
    if r.kalemler:
        print(f"\n{'ÜRÜNLER' if r.birim == 'Ürün' else 'KAMPANYALAR'} (harcamaya göre)")
        for k in r.kalemler[:20]:
            print(_satir(k, 34, r.maliyet_var))
        if len(r.kalemler) > 20:
            print(f"  … ve {len(r.kalemler) - 20} kalem daha (tamamı Excel dosyasında)")
    if r.terimler:
        print("\nARAMA TERİMLERİ (harcamaya göre)")
        for t in r.terimler[:15]:
            print(_satir(t, 34, False))
        if len(r.terimler) > 15:
            print(f"  … ve {len(r.terimler) - 15} terim daha (tamamı Excel dosyasında)")
    print(f"\nBULGULAR VE ÖNERİLER ({len(r.oneriler)})")
    for no, o in enumerate(r.oneriler, 1):
        print(f"  {no}. [{o.tur}] {o.baslik}\n     Bulgu: {o.bulgu}\n     Öneri: {o.oneri}")
    if not r.oneriler:
        print("  Bu raporda kural eşiklerini aşan bir bulgu çıkmadı.")
    for u in r.uyarilar:
        print(f"\nNot: {u}")
    print(f"\n{UYARI}")


def cikti_kodlamasini_ayarla() -> None:
    """Türkçe harfleri gösteremeyen bir ortamda çıktı yazarken çökmeyi önler."""
    for akis in (sys.stdout, sys.stderr):
        ayarla = getattr(akis, "reconfigure", None)
        if ayarla is None:
            continue
        if (getattr(akis, "encoding", None) or "").lower().replace("_", "-") in ("ascii", "us-ascii", "ansi-x3.4-1968", "646"):
            ayarla(encoding="utf-8", errors="replace")
        else:
            ayarla(errors="replace")


def _elle(degerler: list[str]) -> dict[str, str]:
    sonuc = {}
    for d in degerler or []:
        if "=" not in d:
            raise OkumaHatasi(f"--sutun alan=\"Sütun adı\" biçiminde olmalı, ör. --sutun harcama=\"Harcanan Tutar\"; verilen: {d}")
        alan, ad = d.split("=", 1)
        sonuc[alan.strip().lower()] = ad.strip().strip('"').strip("'")
    return sonuc


def main(argv: list[str] | None = None) -> int:
    cikti_kodlamasini_ayarla()
    p = argparse.ArgumentParser(description="Reklam raporundan harcama, satış, reklam getirisi, kâr; bulgular ve öneriler.")
    alt = p.add_subparsers(dest="komut", required=True)
    sq = alt.add_parser("sutunlar", help="Dosyadaki sütunları ve hangisinin neye eşlendiğini gösterir")
    sq.add_argument("dosya")
    sq.add_argument("--sutun", action="append", metavar="ALAN=SÜTUN", help="Eşleştirmeyi elle verir")
    q = alt.add_parser("analiz", help="Reklam raporunu analiz eder")
    q.add_argument("dosya", help="Reklam raporu (.csv ya da .xlsx)")
    q.add_argument("--maliyet", metavar="DOSYA", help="Ürün maliyetleri (.csv/.xlsx): ürün; maliyet; komisyon; kargo; satış fiyatı")
    q.add_argument("--kar-marji", type=float, metavar="YÜZDE",
                   help="Maliyet dosyası yoksa reklam öncesi kâr payınız (satış fiyatının yüzdesi), ör. 25")
    q.add_argument("--sutun", action="append", metavar="ALAN=SÜTUN",
                   help="Tanınmayan sütunu elle eşler; alanlar: " + ", ".join(ALAN_ADLARI))
    q.add_argument("--excel", metavar="DOSYA", help="Sonucu Excel dosyası olarak da kaydeder, ör. sonuc.xlsx")
    q.add_argument("--rapor", metavar="DOSYA", help="Rapor sayfasını (HTML) kaydeder, ör. rapor.html")
    q.add_argument("--baslik", default="", help="Rapor sayfasının başlığı, ör. \"Mağazam: Eylül reklam raporu\"")
    q.add_argument("--tarih", metavar="YYYY-AA-GG", help="Rapor tarihi; verilmezse bugün")
    a = p.parse_args(argv)

    if a.komut == "sutunlar":
        try:
            basliklar, esleme = sutunlari_goster(a.dosya, _elle(a.sutun))
        except OkumaHatasi as hata:
            print(f"Hata: {hata}", file=sys.stderr)
            return 1
        print("DOSYADAKİ SÜTUNLAR")
        for b in basliklar:
            if b:
                print(f"  {b}")
        print("\nEŞLEŞTİRME")
        for alan, sutun in esleme.items():
            print(f"  {ALAN_ADLARI[alan]:<14} ← {sutun if sutun else '(bulunamadı)'}")
        return 0

    try:
        satirlar = oku(a.dosya, _elle(a.sutun))
        maliyetler = maliyet_oku(a.maliyet) if a.maliyet else None
        r = analiz_et(satirlar, maliyetler, a.kar_marji)
    except (OkumaHatasi, ValueError) as hata:
        print(f"Hata: {hata}", file=sys.stderr)
        return 1
    try:
        bugun = date.fromisoformat(a.tarih) if a.tarih else date.today()
    except ValueError:
        print("Hata: --tarih YYYY-AA-GG biçiminde olmalı, ör. 2026-10-14", file=sys.stderr)
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
            yol.write_bytes(dosya(r))
        except OSError as hata:
            print(f"Hata: Excel dosyası yazılamadı: {hata}", file=sys.stderr)
            return 1
        print(f"\nExcel dosyası kaydedildi: {yol}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
