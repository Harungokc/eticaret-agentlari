"""Yorumları dosyadan okur: CSV (yorum;puan) ya da düz metin (.txt). Araç hiçbir siteye bağlanmaz."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from analiz import Yorum


class OkumaHatasi(Exception):
    pass


_YORUM = ("yorum", "yorumlar", "metin", "yorum metni", "degerlendirme", "değerlendirme", "comment", "review", "text")
_PUAN = ("puan", "yildiz", "yıldız", "rating", "star", "stars")
_SATIR_PUANI = re.compile(r"^\s*([1-5])\s*(?:yıldız|yildiz|/\s*5)?\s*[|;\t:–-]\s*(.+)$", re.IGNORECASE | re.DOTALL)


def _puan(deger) -> int | None:
    m = re.search(r"[1-5]", str(deger or ""))
    if not m:
        return None
    try:
        sayi = float(str(deger).strip().replace(",", ".").split("/")[0].split()[0])
    except (ValueError, IndexError):
        sayi = float(m.group())
    return int(round(sayi)) if 1 <= sayi <= 5 else None


def _csv(yol: Path) -> list[Yorum]:
    with open(yol, encoding="utf-8-sig", newline="") as f:
        ornek = f.read(4096)
        f.seek(0)
        ilk = ornek.splitlines()[0] if ornek.splitlines() else ""
        ayirici = ";" if ilk.count(";") >= ilk.count(",") and ";" in ilk else ("," if "," in ilk else ";")
        okur = csv.DictReader(f, delimiter=ayirici)
        basliklar = {(b or "").strip().lower(): b for b in (okur.fieldnames or [])}
        yorum_sutunu = next((basliklar[a] for a in _YORUM if a in basliklar), None)
        puan_sutunu = next((basliklar[a] for a in _PUAN if a in basliklar), None)
        if yorum_sutunu is None:
            raise OkumaHatasi("Dosyada 'yorum' sütunu bulunamadı. İlk satır şu başlıkları içermeli: yorum;puan")
        return [Yorum((s.get(yorum_sutunu) or "").strip(), _puan(s.get(puan_sutunu)) if puan_sutunu else None) for s in okur]


def _txt(yol: Path) -> list[Yorum]:
    """Yorumlar boş satırla ayrılmışsa öyle, değilse her satır bir yorum sayılır. Satır "4 | metin" diye başlayabilir."""
    metin = yol.read_text(encoding="utf-8-sig")
    bloklar = [b.strip() for b in re.split(r"\n\s*\n", metin)] if re.search(r"\n\s*\n", metin) else metin.splitlines()
    yorumlar = []
    for b in bloklar:
        b = b.strip()
        if not b:
            continue
        m = _SATIR_PUANI.match(b)
        yorumlar.append(Yorum(m.group(2).strip(), int(m.group(1))) if m else Yorum(b))
    return yorumlar


def oku(yol: str | Path) -> list[Yorum]:
    yol = Path(yol)
    if not yol.exists():
        raise OkumaHatasi(f"Dosya bulunamadı: {yol}")
    try:
        if yol.suffix.lower() == ".csv":
            yorumlar = _csv(yol)
        elif yol.suffix.lower() == ".txt":
            yorumlar = _txt(yol)
        else:
            raise OkumaHatasi(f"Bu araç yorumları .csv ya da .txt dosyasından okur; verilen dosya: {yol.name}")
    except UnicodeDecodeError:
        raise OkumaHatasi("Dosya okunamadı. Dosyayı UTF-8 olarak kaydedin.") from None
    yorumlar = [y for y in yorumlar if len(y.metin) >= 3]
    if not yorumlar:
        raise OkumaHatasi("Dosyada okunabilen yorum bulunamadı")
    return yorumlar
