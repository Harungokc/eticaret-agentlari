"""Yorum Analizcisi — komut satırı.

Bir ürünün yorumlarından müşterinin ne istediğini çıkarır:

    python agent.py analiz yorumlar.csv
    python agent.py analiz yorumlar.txt --excel sonuc.xlsx
    python agent.py analiz yorumlar.csv --konu "Kapak ve sızdırma=kapak,sızdır,conta"
    python agent.py konular                      aracın tanıdığı konu başlıkları

Hazır konular her ürüne uymaz. İlk çalıştırmada "sık geçen kelimeler" bölümüne bakın, ürününüze özgü
konuları --konu ile tanımlayıp yeniden çalıştırın.

Araç hiçbir siteye bağlanmaz; yorumları siz verirsiniz. Ek paket gerekmez (Python 3.10+).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analiz import KONULAR, Rapor, analiz_et
from okuyucu import OkumaHatasi, oku
from rapor import UYARI, dosya


def _yuzde(adet: int, toplam: int) -> str:
    return f"%{round(100 * adet / toplam)}" if toplam else "%0"


def yaz(r: Rapor) -> None:
    n = r.yorum_sayisi
    print(f"YORUM ANALİZİ — {n} yorum")
    if r.puanli:
        dagilim = "  ".join(f"{y}★ {r.puan_dagilimi[y]}" for y in (5, 4, 3, 2, 1))
        print(f"  Ortalama puan: {r.ortalama_puan:.1f}".replace(".", ",") + f" ({r.puanli} puanlı yorum)   {dagilim}")
    print(f"  Olumlu {r.olumlu} ({_yuzde(r.olumlu, n)})   Nötr {r.notr} ({_yuzde(r.notr, n)})   Olumsuz {r.olumsuz} ({_yuzde(r.olumsuz, n)})")

    print("\nKONULAR (şikâyeti çok olan önce; sayılar yorum adedidir)")
    if not r.konular:
        print("  Yorumlarda tanınan bir konu geçmiyor.")
    for k in r.konular:
        print(f"  {k.ad:<34} söz eden {k.yorum_sayisi:>3}   şikâyet {k.sikayet:>3}   övgü {k.ovgu:>3}")
    sikayetli = [k for k in r.konular if k.sikayet]
    if sikayetli:
        print("\nEN ÇOK ŞİKÂYET EDİLENLER")
        for k in sikayetli[:4]:
            print(f"  {k.ad} — {k.sikayet} yorum")
            for ornek in k.sikayet_ornekleri:
                print(f"    “{ornek}”")

    print(f"\nMÜŞTERİ TALEPLERİ — {r.talep_iceren_yorum} yorumda")
    if not r.talepler:
        print("  Açık bir talep ifadesi (“keşke”, “olsaydı”, “tek eksiği” vb.) bulunamadı.")
    for cumle, konular in r.talepler[:12]:
        print(f"  “{cumle}”" + (f"  [{', '.join(konular)}]" if konular else ""))
    if len(r.talepler) > 12:
        print(f"  … ve {len(r.talepler) - 12} talep daha (tamamı Excel dosyasında)")

    if r.konusuz_sikayetler:
        print("\nHAZIR KONULARA GİRMEYEN ŞİKÂYETLER")
        for cumle in r.konusuz_sikayetler[:6]:
            print(f"  “{cumle}”")
    if r.olumsuz_kelimeler:
        print("\nŞİKÂYET VE TALEPLERDE SIK GEÇEN KELİMELER (kaç yorumda; ekleriyle birlikte sayılır)")
        print("  " + ", ".join(f"{k} ({a})" for k, a in r.olumsuz_kelimeler[:15]))
        print("  Ürününüze özgü bir sorun görüyorsanız --konu ile ayrı bir konu olarak saydırabilirsiniz.")
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
    p = argparse.ArgumentParser(description="Ürün yorumlarından konular, şikâyetler ve müşteri talepleri.")
    alt = p.add_subparsers(dest="komut", required=True)
    q = alt.add_parser("analiz", help="Yorum dosyasını analiz eder")
    q.add_argument("dosya", help="Yorumlar (.csv: yorum;puan sütunları ya da .txt: her satır bir yorum)")
    q.add_argument("--konu", action="append", default=[], metavar="AD=KELİMELER",
                   help='Bu ürüne özgü ek konu, ör. "Kapak ve sızdırma=kapak,sızdır,conta". Birden çok kez verilebilir')
    q.add_argument("--excel", metavar="DOSYA", help="Sonucu Excel dosyası olarak da kaydeder, ör. sonuc.xlsx")
    alt.add_parser("konular", help="Aracın tanıdığı konu başlıklarını listeler")
    a = p.parse_args(argv)

    if a.komut == "konular":
        for ad in KONULAR:
            print(f"- {ad}")
        return 0
    try:
        ek_konular = {}
        for tanim in a.konu:
            ad, ayrac, kelimeler = tanim.partition("=")
            if not ayrac:
                raise ValueError(f"Ek konu anlaşılamadı: {tanim!r}. Şu biçimde verin: Konu adı=kelime1,kelime2")
            ek_konular.setdefault(ad.strip(), []).extend(kelimeler.split(","))
        yorumlar = oku(a.dosya)
        r = analiz_et(yorumlar, ek_konular)
    except (OkumaHatasi, ValueError) as hata:
        print(f"Hata: {hata}", file=sys.stderr)
        return 1
    yaz(r)
    if a.excel:
        yol = Path(a.excel).expanduser()
        if yol.suffix.lower() != ".xlsx":
            yol = yol.with_suffix(".xlsx")
        try:
            yol.write_bytes(dosya(yorumlar, r))
        except OSError as hata:
            print(f"Hata: Excel dosyası yazılamadı: {hata}", file=sys.stderr)
            return 1
        print(f"\nExcel dosyası kaydedildi: {yol}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
