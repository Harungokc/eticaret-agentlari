"""Araçları, Claude'a Skill olarak ya da ChatGPT'ye dosya olarak yüklenebilen ZIP dosyalarına çevirir.

Her aracın talimatları kendi klasöründeki SKILL.md dosyasındadır.

Çalıştırmak için: python paket/paket_olustur.py
"""

import zipfile
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
CIKTI = Path(__file__).resolve().parent

PAKETLER = {
    "pazar-komisyon-analizcisi": ("01-pazar-ve-komisyon-analizcisi", [
        "SKILL.md", "agent.py", "komisyon.py", "pazar.py", "okuyucu.py", "excel.py", "sheets.py",
        "veri/komisyon.json", "ornek/ornek_urunler.csv", "ornek/sablon.csv"]),
    "urun-fiyat-rakip-analizcisi": ("02-urun-fiyat-ve-rakip-analizcisi", [
        "SKILL.md", "agent.py", "analiz.py", "okuyucu.py", "rapor.py", "xlsx.py",
        "ornek/ornek_urunler.csv", "ornek/sablon.csv"]),
    "yorum-analizcisi": ("03-yorum-analizcisi", [
        "SKILL.md", "agent.py", "analiz.py", "okuyucu.py", "rapor.py", "xlsx.py",
        "ornek/ornek_yorumlar.csv", "ornek/sablon.csv"]),
}
SABIT_TARIH = (2026, 1, 1, 0, 0, 0)  # aynı içerik her seferinde aynı ZIP'i üretsin


def ekle(z: zipfile.ZipFile, yol: str, icerik: bytes) -> None:
    bilgi = zipfile.ZipInfo(yol, SABIT_TARIH)
    bilgi.compress_type = zipfile.ZIP_DEFLATED
    bilgi.external_attr = 0o644 << 16
    z.writestr(bilgi, icerik)


def main() -> None:
    for ad, (klasor, dosyalar) in PAKETLER.items():
        hedef = CIKTI / f"{ad}.zip"
        with zipfile.ZipFile(hedef, "w") as z:
            for dosya in dosyalar:
                ekle(z, f"{ad}/{dosya}", (KOK / klasor / dosya).read_bytes())
            ekle(z, f"{ad}/LICENSE", (KOK / "LICENSE").read_bytes())
        print(f"{hedef}  ({hedef.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
