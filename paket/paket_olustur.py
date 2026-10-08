"""Aracı, Claude'a Skill olarak ya da ChatGPT'ye dosya olarak yüklenebilen tek bir ZIP hâline getirir.

Çalıştırmak için: python paket/paket_olustur.py
"""

import zipfile
from pathlib import Path

AD = "pazar-komisyon-analizcisi"
KOK = Path(__file__).resolve().parent.parent
ARAC = KOK / "01-pazar-ve-komisyon-analizcisi"
CIKTI = Path(__file__).resolve().parent / f"{AD}.zip"

DOSYALAR = ["agent.py", "komisyon.py", "pazar.py", "okuyucu.py", "excel.py", "sheets.py",
            "veri/komisyon.json", "ornek/ornek_urunler.csv", "ornek/sablon.csv"]
SABIT_TARIH = (2026, 1, 1, 0, 0, 0)  # aynı içerik her seferinde aynı ZIP'i üretsin


def ekle(z: zipfile.ZipFile, ad: str, icerik: bytes) -> None:
    bilgi = zipfile.ZipInfo(f"{AD}/{ad}", SABIT_TARIH)
    bilgi.compress_type = zipfile.ZIP_DEFLATED
    bilgi.external_attr = 0o644 << 16
    z.writestr(bilgi, icerik)


def main() -> None:
    with zipfile.ZipFile(CIKTI, "w") as z:
        ekle(z, "SKILL.md", (Path(__file__).parent / "SKILL.md").read_bytes())
        ekle(z, "LICENSE", (KOK / "LICENSE").read_bytes())
        for ad in DOSYALAR:
            ekle(z, ad, (ARAC / ad).read_bytes())
    print(f"{CIKTI}  ({CIKTI.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
