"""Pazar ve Komisyon Analizcisi — komut satırı.

Kullanım:
    python agent.py komisyon "kadın ayakkabı" 899
    python agent.py komisyon "telefon kılıfı" 249 --maliyet 80 --trendyol 26
    python agent.py pazar arama.html --kategori "erkek parfüm"
    python agent.py pazar urunler.csv --kategori kozmetik --maliyet 180
    python agent.py komisyon giyim 599 --excel sonuc.xlsx
    python agent.py kategoriler
"""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

from excel import kitap_yaz, komisyon_sayfalari, pazar_sayfalari
from komisyon import Satir, analiz_et, kategori_bul, kesin_mi, veri_yukle
from okuyucu import OkumaHatasi, oku, sayi
from pazar import PazarRaporu
from pazar import analiz_et as pazar_analiz_et


def tl(x: float | None) -> str:
    if x is None:
        return "-"
    return f"{x:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")


def tl0(x: float) -> str:
    return f"{x:,.0f} TL".replace(",", ".")


def aralik(a: float | None, b: float | None, bicim) -> str:
    if a is None:
        return "veri yok"
    return bicim(a) if a == b else f"{bicim(a)} – {bicim(b)}"


def yuzde(x: float) -> str:
    return f"%{x:g}".replace(".", ",")


def sayi_cevir(metin: str) -> float:
    """"1.299,90", "1299.90" ve "1.000" (bin) biçimlerini kabul eder; anlaşılmazsa ValueError."""
    sonuc = sayi(metin)
    if sonuc is None or not any(k.isdigit() for k in metin):
        raise ValueError(f"sayı anlaşılamadı: {metin!r}")
    return sonuc


def _tablo(satirlar: list[list[str]]) -> list[str]:
    genislik = [max(len(r[i]) for r in satirlar) for i in range(len(satirlar[0]))]
    cikti = []
    for i, r in enumerate(satirlar):
        cikti.append("  ".join(h.ljust(genislik[j]) for j, h in enumerate(r)).rstrip())
        if i == 0:
            cikti.append("  ".join("-" * g for g in genislik))
    return cikti


# ---------------------------------------------------------------- komisyon raporu

def komisyon_raporu(kategori: dict, fiyat: float, satirlar: list[Satir], maliyet: float | None, veri: dict) -> str:
    cikti = [f"Kategori: {kategori['ad']}    Satış fiyatı: {tl(fiyat)}"
             + (f"    Ürün maliyeti: {tl(maliyet)}" if maliyet is not None else ""), ""]

    basliklar = ["Pazaryeri", "Komisyon oranı", "Komisyon", "Ele geçen"] + (["Kâr"] if maliyet is not None else [])
    tablo = [basliklar]
    for s in satirlar:
        satir = [s.ad, aralik(s.oran_min, s.oran_max, yuzde), aralik(s.komisyon_min, s.komisyon_max, tl),
                 aralik(s.ele_gecen_min, s.ele_gecen_max, tl)]
        if maliyet is not None:
            satir.append(aralik(s.kar_min, s.kar_max, tl))
        tablo.append(satir)
    cikti += _tablo(tablo) + [""]

    dolu = [s for s in satirlar if s.ele_gecen_min is not None]
    if dolu:
        en_iyi = dolu[0]
        if len(dolu) == 1:
            cikti.append(f"Yalnızca {en_iyi.ad} için oran bulundu; karşılaştırma yapılamadı.")
        elif kesin_mi(satirlar):
            cikti.append(f"Sonuç: bu kategoride en çok {en_iyi.ad} kazandırıyor "
                         f"(ele geçen {aralik(en_iyi.ele_gecen_min, en_iyi.ele_gecen_max, tl)}).")
        else:
            cikti.append(f"Sonuç: ortalamada {en_iyi.ad} önde, ama oran aralıkları {dolu[1].ad} ile çakışıyor; "
                         "kesin sıralama için kendi sözleşme oranlarınızı girin.")
    eksik = [s.ad for s in satirlar if s.ele_gecen_min is None]
    if eksik:
        cikti.append(f"Oran bulunamayanlar: {', '.join(eksik)}. Kendi oranınızı girerek ekleyebilirsiniz.")
    girilen = [s.ad for s in satirlar if s.kaynak == "satıcının girdiği oran"]
    if girilen:
        cikti.append(f"Sizin girdiğiniz oran kullanıldı: {', '.join(girilen)}.")

    cikti += ["", "Hesaba dahil olanlar ve olmayanlar:"]
    for s in dolu:
        if s.notu:
            cikti.append(f"- {s.ad}: {s.notu}")
    cikti += [
        "- Kargo, sabit hizmet bedeli, stopaj, reklam ve iade maliyeti hiçbir pazaryerinde hesaba dahil değil.",
        "",
        f"Oranlar yaklaşık değerlerdir (derleme: {veri['_derleme_tarihi']}). Pazaryerleri oranları açık tek bir tabloda",
        "yayımlamıyor; bağlayıcı oran satıcı panelinizdeki sözleşme ekranındadır.",
    ]
    adresler = sorted({a for s in dolu for a in s.kaynak_adresleri})
    if adresler:
        cikti += ["", "Kaynaklar:"] + [f"- {a}" for a in adresler]
    return "\n".join(cikti)


# ---------------------------------------------------------------- pazar raporu

def pazar_raporu(r: PazarRaporu, dosya: str) -> str:
    cikti = [f"PAZAR ANALİZİ — {dosya}", ""]
    boyut = f"{r.urun_sayisi} ürün, {r.marka_sayisi} marka"
    if r.satici_sayisi:
        boyut += f", {r.satici_sayisi} satıcı"
    cikti += [f"İncelenen: {boyut}", ""]

    cikti += ["Fiyat", *_tablo([
        ["En düşük", "Alt çeyrek", "Ortanca", "Üst çeyrek", "En yüksek", "Ortalama"],
        [tl0(r.fiyat_min), tl0(r.fiyat_ceyrek1), tl0(r.fiyat_medyan), tl0(r.fiyat_ceyrek3), tl0(r.fiyat_max),
         tl0(r.fiyat_ortalama)],
    ]), f"Ürünlerin yarısı {tl0(r.fiyat_ceyrek1)} ile {tl0(r.fiyat_ceyrek3)} arasında.", ""]

    bant = [["Fiyat bandı", "Ürün", "Ürün başına ortalama yorum"]]
    for b in r.bantlar:
        bant.append([f"{tl0(b.alt)} – {tl0(b.ust)}", str(b.urun_sayisi),
                     "-" if b.ortalama_yorum is None else f"{b.ortalama_yorum:,.0f}".replace(",", ".")])
    cikti += ["Fiyat bantları", *_tablo(bant), ""]

    if r.markalar:
        cikti += ["Öne çıkan markalar",
                  *_tablo([["Marka", "Ürün", "Pay"]] + [[m, str(n), yuzde(p)] for m, n, p in r.markalar]), ""]

    if r.yorum_medyan is not None:
        cikti.append("İlgi ve rekabet")
        if r.puan_medyan is not None:
            cikti.append(f"- Ortanca puan: {str(r.puan_medyan).replace('.', ',')}")
        cikti.append(f"- Ortanca yorum sayısı: {r.yorum_medyan:,.0f}".replace(",", "."))
        if r.ilk10_yorum_payi is not None:
            cikti.append(f"- En çok yorumlanan 10 ürün, toplam yorumların {yuzde(r.ilk10_yorum_payi)} kadarını topluyor "
                         f"(pazar {r.yogunluk}).")
        cikti.append("")

    cikti.append("Okuma")
    if r.yogunluk == "yoğunlaşmış":
        cikti.append("- İlgi birkaç üründe toplanmış; yeni bir ürünün görünür olması zor, fiyat veya farklılaşma gerekir.")
    elif r.yogunluk == "orta":
        cikti.append("- İlgi birkaç güçlü ürünle geri kalanlar arasında bölünmüş; öne çıkmak mümkün ama yorum birikimi gerekir.")
    elif r.yogunluk == "dağınık":
        cikti.append("- İlgi ürünlere yayılmış; tek bir hâkim ürün yok, yeni girişe görece açık.")
    if r.bosluk:
        cikti.append(f"- {tl0(r.bosluk.alt)} – {tl0(r.bosluk.ust)} bandında yalnızca {r.bosluk.urun_sayisi} ürün var, "
                     "ama ürün başına yorum ortancanın üstünde: bu bant az rakipli ve ilgi görüyor.")
    else:
        cikti.append("- Belirgin biçimde boş kalan ve ilgi gören bir fiyat bandı görünmüyor.")
    for u in r.uyarilar:
        cikti.append(f"- Not: {u}")
    cikti += ["",
              "Bu analiz yalnızca verdiğiniz dosyadaki ürünleri kapsar. Satış adedi ve ciro bilgisi içermez; yorum",
              "sayısı ilginin dolaylı göstergesidir."]
    return "\n".join(cikti)


# ---------------------------------------------------------------- komutlar

def _kategori_coz(metin: str, veri: dict):
    e = kategori_bul(metin, veri)
    if e.kategori is None:
        print(f'"{metin}" için kategori bulunamadı.')
        if e.adaylar:
            print("Şunlardan biri olabilir: " + ", ".join(e.adaylar))
        print("Tüm kategoriler için: python agent.py kategoriler")
        return None
    if e.nasil == "benzer":
        print(f'Not: "{metin}" → {e.kategori["ad"]} olarak yorumlandı.\n')
    return e.kategori


def _excel_kaydet(yol: str, icerik: bytes) -> None:
    hedef = Path(yol)
    if hedef.suffix.lower() != ".xlsx":
        hedef = hedef.with_suffix(".xlsx")
    hedef.write_bytes(icerik)
    print(f"\nExcel dosyası kaydedildi: {hedef}")


def _cikti(a, sayfalar: list) -> int:
    """İstenmişse sonucu Excel dosyasına ve/veya Google Sheets tablosuna yazar."""
    if a.excel:
        _excel_kaydet(a.excel, kitap_yaz(sayfalar))
    if a.sheets:
        if not a.anahtar:
            print("\nHata: Google Sheets'e yazmak için --anahtar ile hizmet hesabı anahtar dosyasını da verin.")
            return 1
        from sheets import SheetsHatasi, tabloya_yaz
        try:
            sonuc = tabloya_yaz(a.sheets, a.anahtar, sayfalar)
        except SheetsHatasi as hata:
            print(f"\nGoogle Sheets hatası: {hata}")
            return 1
        print(f"\nGoogle Sheets'e yazıldı ({', '.join(sonuc['sekmeler'])}): {sonuc['adres']}")
        if sonuc["hatali_hucre"]:
            print(f"Uyarı: {sonuc['hatali_hucre']} hücre hata gösteriyor; tabloyu açıp kontrol edin.")
    return 0


def _kendi_oranlar(a, veri: dict) -> dict[str, float]:
    return {k: getattr(a, k) for k in veri["pazaryerleri"] if getattr(a, k, None) is not None}


def komut_komisyon(a, veri: dict) -> int:
    kategori = _kategori_coz(a.kategori, veri)
    if kategori is None:
        return 1
    fiyat = sayi_cevir(a.fiyat)
    maliyet = sayi_cevir(a.maliyet) if a.maliyet else None
    satirlar = analiz_et(kategori, fiyat, veri, maliyet, _kendi_oranlar(a, veri))
    print(komisyon_raporu(kategori, fiyat, satirlar, maliyet, veri))
    return _cikti(a, komisyon_sayfalari(kategori["ad"], fiyat, maliyet, satirlar, veri))


def komut_pazar(a, veri: dict) -> int:
    try:
        urunler = oku(a.dosya)
        rapor = pazar_analiz_et(urunler)
    except (OkumaHatasi, ValueError) as hata:
        print(f"Hata: {hata}")
        return 1
    print(pazar_raporu(rapor, a.dosya))
    if not a.kategori:
        print('\nKomisyon karşılaştırması için --kategori ekleyin, ör. --kategori "erkek parfüm".')
        return _cikti(a, pazar_sayfalari(rapor, urunler, None, veri))
    kategori = _kategori_coz(a.kategori, veri)
    if kategori is None:
        return 1
    maliyet = sayi_cevir(a.maliyet) if a.maliyet else None
    fiyat = rapor.fiyat_medyan
    print("\n" + "=" * 72)
    print(f"KOMİSYON KARŞILAŞTIRMASI — pazarın ortanca fiyatı ({tl(fiyat)}) üzerinden\n")
    satirlar = analiz_et(kategori, fiyat, veri, maliyet, _kendi_oranlar(a, veri))
    print(komisyon_raporu(kategori, fiyat, satirlar, maliyet, veri))
    return _cikti(a, pazar_sayfalari(rapor, urunler, (kategori["ad"], maliyet, satirlar), veri))


def main(argv: list[str] | None = None) -> int:
    veri = veri_yukle()
    p = argparse.ArgumentParser(description="Pazar analizi ve pazaryeri komisyon karşılaştırması.")
    alt = p.add_subparsers(dest="komut", required=True)

    def oran_secenekleri(q):
        q.add_argument("--maliyet", help="Ürün maliyeti (TL); verilirse kâr da hesaplanır")
        q.add_argument("--excel", metavar="DOSYA", help="Sonucu Excel dosyası olarak da kaydeder, ör. sonuc.xlsx")
        q.add_argument("--sheets", metavar="ADRES", help="Sonucu bu Google Sheets tablosuna yazar (tablonun adresi)")
        q.add_argument("--anahtar", metavar="DOSYA", help="Google hizmet hesabı anahtarı (JSON); --sheets ile birlikte gerekir")
        for anahtar, pz in veri["pazaryerleri"].items():
            q.add_argument(f"--{anahtar}", type=float, metavar="ORAN",
                           help=f"{pz['ad']} için kendi sözleşme oranınız (%%)")

    k = alt.add_parser("komisyon", help="Kategori ve fiyata göre komisyonları karşılaştırır")
    k.add_argument("kategori", help='Ürün veya kategori, ör. "kadın ayakkabı"')
    k.add_argument("fiyat", help="Satış fiyatı (TL)")
    oran_secenekleri(k)

    z = alt.add_parser("pazar", help="Bir ürün listesinden pazar analizi çıkarır")
    z.add_argument("dosya", help="Kaydedilmiş arama sayfası (.html) ya da ürün listesi (.csv, .json)")
    z.add_argument("--kategori", help="Verilirse ortanca fiyat üzerinden komisyon karşılaştırması da eklenir")
    oran_secenekleri(z)

    alt.add_parser("kategoriler", help="Komisyon tablosundaki kategorileri listeler")

    a = p.parse_args(argv)
    try:
        if a.komut == "kategoriler":
            for kat in veri["kategoriler"]:
                print(f"- {kat['ad']}")
            return 0
        if a.komut == "komisyon":
            return komut_komisyon(a, veri)
        return komut_pazar(a, veri)
    except ValueError as hata:
        print(f"Hata: {hata}. Fiyat ve maliyet sayı olmalı, ör. 899 veya 1.299,90")
        return 1


if __name__ == "__main__":
    sys.exit(main())
