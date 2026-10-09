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
    "satis-bolge-analizcisi": ("04-satis-bolge-analizcisi", [
        "SKILL.md", "agent.py", "analiz.py", "okuyucu.py", "rapor.py", "xlsx.py",
        "ornek/ornek_siparisler.csv", "ornek/sablon.csv"]),
}
# Bütün araçları içeren tek paket: her araç kendi alt klasöründe, talimatları TALIMATLAR.md adıyla durur.
TEK_PAKET = "eticaret-analiz-araclari"
ALT_KLASOR = {"pazar-komisyon-analizcisi": "komisyon", "urun-fiyat-rakip-analizcisi": "urun",
              "yorum-analizcisi": "yorum", "satis-bolge-analizcisi": "bolge"}
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

    hedef = CIKTI / f"{TEK_PAKET}.zip"
    with zipfile.ZipFile(hedef, "w") as z:
        ekle(z, f"{TEK_PAKET}/SKILL.md", (CIKTI / "SKILL.md").read_bytes())
        ekle(z, f"{TEK_PAKET}/LICENSE", (KOK / "LICENSE").read_bytes())
        for ad, (klasor, dosyalar) in PAKETLER.items():
            for dosya in dosyalar:
                icerik = (KOK / klasor / dosya).read_bytes()
                if dosya == "SKILL.md":
                    # Alt klasördeki talimat ayrı bir Skill gibi algılanmasın: başlık bloğu atılır, ad değişir.
                    metin = icerik.decode("utf-8")
                    metin = metin.split("---", 2)[2].lstrip("\n") if metin.startswith("---") else metin
                    icerik = metin.replace("SKILL.md", "TALIMATLAR.md").encode("utf-8")
                    dosya = "TALIMATLAR.md"
                ekle(z, f"{TEK_PAKET}/{ALT_KLASOR[ad]}/{dosya}", icerik)
    print(f"{hedef}  ({hedef.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
