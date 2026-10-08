"""Pazar ve Komisyon Analizcisi — tarayıcı arayüzü.

Çalıştırınca bilgisayarınızda küçük bir sayfa açılır; hesap o sayfadaki formlarla yapılır.
Sunucu yalnızca bu bilgisayardan erişilebilir (127.0.0.1) ve internete hiçbir veri göndermez.

    python arayuz.py
"""

from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import threading
import webbrowser
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agent import aralik, sayi_cevir, tl, tl0, yuzde
from excel import kitap_yaz, komisyon_sayfalari, pazar_sayfalari
from komisyon import Satir, analiz_et, kesin_mi, veri_yukle
from okuyucu import OkumaHatasi, oku
from pazar import PazarRaporu
from pazar import analiz_et as pazar_analiz_et
from sheets import Istemci, SheetsHatasi, rsa_anahtari_coz, tablo_kimligi

VERI = veri_yukle()
EN_BUYUK_ISTEK = 15 * 1024 * 1024  # kaydedilmiş bir arama sayfası birkaç MB olabilir
IZINLI_UZANTILAR = (".csv", ".json", ".html", ".htm")
IZINLI_ADRESLER = ("127.0.0.1", "localhost")
SHEETS_HTTP = None  # testlerde sahte ağ katmanı buraya konur


def ayar_klasoru() -> Path:
    """Google Sheets ayarları proje klasörünün DIŞINDA, kullanıcının ana klasöründe tutulur."""
    return Path(os.environ.get("PAZAR_KOMISYON_AYAR") or Path.home() / ".pazar-komisyon")


class GirdiHatasi(Exception):
    pass


# ---------------------------------------------------------------- girdi

def _sayi(deger, ad: str, zorunlu: bool = False) -> float | None:
    metin = str(deger or "").strip()
    if not metin:
        if zorunlu:
            raise GirdiHatasi(f"{ad} boş bırakılamaz.")
        return None
    try:
        sonuc = sayi_cevir(metin)
    except ValueError:
        raise GirdiHatasi(f"{ad} sayı olmalı, ör. 899 veya 1.299,90") from None
    if sonuc < 0:
        raise GirdiHatasi(f"{ad} eksi olamaz.")
    return sonuc


def _kategori(anahtar) -> dict:
    for k in VERI["kategoriler"]:
        if k["anahtar"] == anahtar:
            return k
    raise GirdiHatasi("Lütfen listeden bir kategori seçin.")


def _oranlar(ham) -> dict[str, float]:
    oranlar = {}
    for anahtar, deger in (ham or {}).items():
        if anahtar not in VERI["pazaryerleri"]:
            continue
        oran = _sayi(deger, f"{VERI['pazaryerleri'][anahtar]['ad']} oranı")
        if oran is None:
            continue
        if oran > 60:
            raise GirdiHatasi("Komisyon oranı yüzde olarak yazılmalı, ör. 21,5")
        oranlar[anahtar] = oran
    return oranlar


# ---------------------------------------------------------------- çıktı (HTML)

def _tablo(basliklar: list[str], satirlar: list[list[str]], vurgu: int | None = None) -> str:
    """Hücreler dışarıdan gelen metin içerebilir (ürün ve marka adları); hepsi kaçışlanır."""
    h = "".join(f"<th>{escape(b)}</th>" for b in basliklar)
    g = ""
    for i, s in enumerate(satirlar):
        sinif = ' class="vurgu"' if i == vurgu else ""
        g += f"<tr{sinif}>" + "".join(f"<td>{escape(str(c))}</td>" for c in s) + "</tr>"
    return f'<div class="tablo"><table><thead><tr>{h}</tr></thead><tbody>{g}</tbody></table></div>'


def komisyon_html(kategori: dict, fiyat: float, satirlar: list[Satir], maliyet: float | None) -> str:
    basliklar = ["Pazaryeri", "Komisyon oranı", "Kesilen komisyon", "Elinize geçen"] + (["Kârınız"] if maliyet is not None else [])
    govde = []
    for s in satirlar:
        satir = [s.ad, aralik(s.oran_min, s.oran_max, yuzde), aralik(s.komisyon_min, s.komisyon_max, tl),
                 aralik(s.ele_gecen_min, s.ele_gecen_max, tl)]
        if maliyet is not None:
            satir.append(aralik(s.kar_min, s.kar_max, tl))
        govde.append(satir)
    dolu = [s for s in satirlar if s.ele_gecen_min is not None]

    if not dolu:
        sonuc = "Bu kategori için hiçbir pazaryerinde oran bulunamadı. Kendi oranlarınızı girerek hesaplayabilirsiniz."
    elif len(dolu) == 1:
        sonuc = f"Yalnızca {dolu[0].ad} için oran bulundu; karşılaştırma yapılamadı."
    elif kesin_mi(satirlar):
        sonuc = (f"Bu kategoride en çok {dolu[0].ad} kazandırıyor: elinize "
                 f"{aralik(dolu[0].ele_gecen_min, dolu[0].ele_gecen_max, tl)} geçiyor.")
    else:
        sonuc = (f"Ortalamada {dolu[0].ad} önde, ama oran aralıkları {dolu[1].ad} ile çakışıyor. Kesin sıralama için "
                 "yukarıdaki “Kendi komisyon oranlarım” bölümüne sözleşmenizdeki oranları yazın.")

    cikti = [f"<h3>{escape(kategori['ad'])} — satış fiyatı {escape(tl(fiyat))}"
             + (f", maliyet {escape(tl(maliyet))}" if maliyet is not None else "") + "</h3>",
             f'<p class="sonuc">{escape(sonuc)}</p>',
             _tablo(basliklar, govde, vurgu=0 if dolu else None)]
    notlar = []
    eksik = [s.ad for s in satirlar if s.ele_gecen_min is None]
    if eksik and dolu:
        notlar.append(f"Oran bulunamayanlar: {', '.join(eksik)}. Kendi oranınızı girerek ekleyebilirsiniz.")
    girilen = [s.ad for s in satirlar if s.kaynak == "satıcının girdiği oran"]
    if girilen:
        notlar.append(f"Sizin girdiğiniz oran kullanıldı: {', '.join(girilen)}.")
    notlar += [f"{s.ad}: {s.notu}" for s in dolu if s.notu]
    notlar.append("Kargo, sabit hizmet bedeli, stopaj, reklam ve iade maliyeti hesaba dahil değildir; gerçekte elinize "
                  "geçen tutar daha düşük olur.")
    notlar.append(f"Oranlar yaklaşık değerlerdir (derleme tarihi: {VERI['_derleme_tarihi']}). Bağlayıcı oran, satıcı "
                  "panelinizdeki sözleşme ekranında yazar.")
    cikti.append("<ul class='notlar'>" + "".join(f"<li>{escape(n)}</li>" for n in notlar) + "</ul>")
    return "".join(cikti)


def pazar_html(r: PazarRaporu) -> str:
    boyut = f"{r.urun_sayisi} ürün, {r.marka_sayisi} marka" + (f", {r.satici_sayisi} satıcı" if r.satici_sayisi else "")
    cikti = [f"<h3>Pazar analizi — {escape(boyut)}</h3>"]

    okuma = []
    if r.yogunluk == "yoğunlaşmış":
        okuma.append("İlgi birkaç üründe toplanmış; yeni bir ürünün görünür olması zor, fiyat veya farklılaşma gerekir.")
    elif r.yogunluk == "orta":
        okuma.append("İlgi birkaç güçlü ürünle geri kalanlar arasında bölünmüş; öne çıkmak mümkün ama yorum birikimi gerekir.")
    elif r.yogunluk == "dağınık":
        okuma.append("İlgi ürünlere yayılmış; tek bir hâkim ürün yok, yeni girişe görece açık.")
    if r.bosluk:
        okuma.append(f"{tl0(r.bosluk.alt)} – {tl0(r.bosluk.ust)} bandında yalnızca {r.bosluk.urun_sayisi} ürün var, ama "
                     "ürün başına yorum ortancanın üstünde: bu bant az rakipli ve ilgi görüyor.")
    else:
        okuma.append("Belirgin biçimde boş kalan ve ilgi gören bir fiyat bandı görünmüyor.")
    cikti.append('<p class="sonuc">' + escape(" ".join(okuma)) + "</p>")

    cikti.append("<h4>Fiyatlar</h4>")
    cikti.append(_tablo(["En düşük", "Alt çeyrek", "Ortanca", "Üst çeyrek", "En yüksek", "Ortalama"],
                        [[tl0(r.fiyat_min), tl0(r.fiyat_ceyrek1), tl0(r.fiyat_medyan), tl0(r.fiyat_ceyrek3),
                          tl0(r.fiyat_max), tl0(r.fiyat_ortalama)]]))
    cikti.append(f"<p>Ürünlerin yarısı {escape(tl0(r.fiyat_ceyrek1))} ile {escape(tl0(r.fiyat_ceyrek3))} arasında.</p>")

    cikti.append("<h4>Fiyat bantları</h4>")
    cikti.append(_tablo(["Fiyat bandı", "Ürün sayısı", "Ürün başına ortalama yorum"],
                        [[f"{tl0(b.alt)} – {tl0(b.ust)}", b.urun_sayisi,
                          "-" if b.ortalama_yorum is None else f"{b.ortalama_yorum:,.0f}".replace(",", ".")]
                         for b in r.bantlar]))
    if r.markalar:
        cikti.append("<h4>Öne çıkan markalar</h4>")
        cikti.append(_tablo(["Marka", "Ürün sayısı", "Payı"], [[m, n, yuzde(p)] for m, n, p in r.markalar]))

    ilgi = []
    if r.puan_medyan is not None:
        ilgi.append(f"Ortanca puan: {str(r.puan_medyan).replace('.', ',')}")
    if r.yorum_medyan is not None:
        ilgi.append(f"Ortanca yorum sayısı: {r.yorum_medyan:,.0f}".replace(",", "."))
    if r.ilk10_yorum_payi is not None:
        ilgi.append(f"En çok yorumlanan 10 ürün, toplam yorumların {yuzde(r.ilk10_yorum_payi)} kadarını topluyor "
                    f"(pazar {r.yogunluk}).")
    if ilgi:
        cikti.append("<h4>İlgi ve rekabet</h4><ul>" + "".join(f"<li>{escape(i)}</li>" for i in ilgi) + "</ul>")

    notlar = list(r.uyarilar) + ["Bu analiz yalnızca yüklediğiniz dosyadaki ürünleri kapsar. Satış adedi ve ciro bilgisi "
                                 "içermez; yorum sayısı ilginin dolaylı göstergesidir."]
    cikti.append("<ul class='notlar'>" + "".join(f"<li>{escape(n)}</li>" for n in notlar) + "</ul>")
    return "".join(cikti)


# ---------------------------------------------------------------- işlemler

def _istemci() -> Istemci:
    yol = ayar_klasoru() / "hizmet-hesabi.json"
    try:
        anahtar = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise GirdiHatasi("Google Sheets bağlantısı kurulmamış. Sayfanın altındaki “Google Sheets bağlantısı” bölümünden kurun.") from None
    return Istemci(anahtar, SHEETS_HTTP) if SHEETS_HTTP else Istemci(anahtar)


def _ayar() -> dict:
    try:
        ayar = json.loads((ayar_klasoru() / "ayarlar.json").read_text(encoding="utf-8"))
        return ayar if isinstance(ayar, dict) else {}
    except (OSError, ValueError):
        return {}


def islem_sheets_durum(_: dict) -> dict:
    """Bağlantı kurulu mu? Anahtarın kendisi hiçbir zaman tarayıcıya geri gönderilmez."""
    tablo = _ayar().get("tablo")
    try:
        hesap = _istemci().hesap
    except GirdiHatasi:
        hesap = None
    return {"ayarli": bool(tablo and hesap), "hesap": hesap, "tablo": tablo, "tablo_adi": _ayar().get("tablo_adi")}


def islem_sheets_ayar(g: dict) -> dict:
    try:
        kimlik = tablo_kimligi(str(g.get("tablo") or ""))
    except SheetsHatasi as hata:
        raise GirdiHatasi(str(hata)) from None
    klasor = ayar_klasoru()
    icerik = g.get("anahtar_icerik")
    if icerik:
        try:
            anahtar = json.loads(icerik)
            if not isinstance(anahtar, dict) or anahtar.get("type") != "service_account" or not anahtar.get("client_email"):
                raise ValueError
            rsa_anahtari_coz(str(anahtar.get("private_key") or ""))
        except (ValueError, SheetsHatasi):
            raise GirdiHatasi("Seçtiğiniz dosya bir hizmet hesabı anahtarı değil. Google Cloud'da hizmet hesabı için "
                              "indirdiğiniz JSON dosyasını seçin.") from None
        klasor.mkdir(parents=True, exist_ok=True)
        yol = klasor / "hizmet-hesabi.json"
        yol.write_text(json.dumps(anahtar), encoding="utf-8")
        try:
            yol.chmod(0o600)  # yalnızca bu kullanıcı okuyabilsin
        except OSError:
            pass
    istemci = _istemci()  # anahtar hiç yüklenmemişse burada anlaşılır hata verir
    try:
        bilgi = istemci._cagir("GET", f"{kimlik}?fields=properties.title")
    except SheetsHatasi as hata:
        raise GirdiHatasi(str(hata)) from None
    tablo_adi = (bilgi.get("properties") or {}).get("title") or ""
    klasor.mkdir(parents=True, exist_ok=True)
    (klasor / "ayarlar.json").write_text(json.dumps({"tablo": f"https://docs.google.com/spreadsheets/d/{kimlik}/edit",
                                                      "tablo_adi": tablo_adi}, ensure_ascii=False), encoding="utf-8")
    return islem_sheets_durum({})


def islem_sheets_kaldir(_: dict) -> dict:
    for ad in ("hizmet-hesabi.json", "ayarlar.json"):
        (ayar_klasoru() / ad).unlink(missing_ok=True)
    return islem_sheets_durum({})


def _yanit(html: str, sayfalar: list, dosya_adi: str, sheets_iste: bool) -> dict:
    yanit = {"html": html, "excel": base64.b64encode(kitap_yaz(sayfalar)).decode("ascii"), "excel_adi": dosya_adi}
    if sheets_iste:
        tablo = _ayar().get("tablo")
        if not tablo:
            raise GirdiHatasi("Google Sheets bağlantısı kurulmamış. Sayfanın altındaki “Google Sheets bağlantısı” bölümünden kurun.")
        try:
            yanit["sheets"] = _istemci().yaz(tablo, sayfalar)
        except SheetsHatasi as hata:
            raise GirdiHatasi(str(hata)) from None
    return yanit


def islem_komisyon(g: dict) -> dict:
    kategori = _kategori(g.get("kategori"))
    fiyat = _sayi(g.get("fiyat"), "Satış fiyatı", zorunlu=True)
    if fiyat <= 0:
        raise GirdiHatasi("Satış fiyatı sıfırdan büyük olmalı.")
    maliyet = _sayi(g.get("maliyet"), "Ürün maliyeti")
    satirlar = analiz_et(kategori, fiyat, VERI, maliyet, _oranlar(g.get("oranlar")))
    return _yanit(komisyon_html(kategori, fiyat, satirlar, maliyet),
                  komisyon_sayfalari(kategori["ad"], fiyat, maliyet, satirlar, VERI), "komisyon-karsilastirmasi.xlsx",
                  bool(g.get("sheets")))


def islem_pazar(g: dict) -> dict:
    ad, icerik = str(g.get("dosya_adi") or ""), g.get("icerik")
    if not ad or not isinstance(icerik, str) or not icerik.strip():
        raise GirdiHatasi("Lütfen bir dosya seçin.")
    uzanti = Path(ad).suffix.lower()
    if uzanti not in IZINLI_UZANTILAR:
        raise GirdiHatasi("Desteklenen dosya türleri: .csv, .json, .html")
    # Dosya adı kullanıcıdan gelir; diskte yalnızca uzantısı kullanılır.
    with tempfile.NamedTemporaryFile("w", suffix=uzanti, encoding="utf-8", delete=False) as gecici:
        gecici.write(icerik)
        yol = Path(gecici.name)
    try:
        urunler = oku(yol)
        rapor = pazar_analiz_et(urunler)
    except (OkumaHatasi, ValueError) as hata:
        raise GirdiHatasi(str(hata)) from None
    finally:
        yol.unlink(missing_ok=True)

    cikti = pazar_html(rapor)
    komisyon = None
    if g.get("kategori"):
        kategori = _kategori(g["kategori"])
        maliyet = _sayi(g.get("maliyet"), "Ürün maliyeti")
        satirlar = analiz_et(kategori, rapor.fiyat_medyan, VERI, maliyet, _oranlar(g.get("oranlar")))
        cikti += ("<hr><p><b>Komisyon karşılaştırması</b> — pazarın ortanca fiyatı üzerinden:</p>"
                  + komisyon_html(kategori, rapor.fiyat_medyan, satirlar, maliyet))
        komisyon = (kategori["ad"], maliyet, satirlar)
    return _yanit(cikti, pazar_sayfalari(rapor, urunler, komisyon, VERI), "pazar-analizi.xlsx", bool(g.get("sheets")))


ISLEMLER = {"/api/komisyon": islem_komisyon, "/api/pazar": islem_pazar, "/api/sheets-durum": islem_sheets_durum,
            "/api/sheets-ayar": islem_sheets_ayar, "/api/sheets-kaldir": islem_sheets_kaldir}


# ---------------------------------------------------------------- sayfa

def sayfa() -> str:
    secenekler = "".join(f'<option value="{escape(k["anahtar"])}">{escape(k["ad"])}</option>' for k in VERI["kategoriler"])
    oran_alanlari = "".join(
        f'<label>{escape(pz["ad"])} (%)<input type="text" inputmode="decimal" data-oran="{escape(a)}" placeholder="ör. 21,5"></label>'
        for a, pz in VERI["pazaryerleri"].items())
    return SAYFA.replace("{{SECENEKLER}}", secenekler).replace("{{ORANLAR}}", oran_alanlari)


SAYFA = """<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pazar ve Komisyon Analizcisi</title>
<style>
:root{--zemin:#f6f7f9;--kart:#fff;--yazi:#1c2430;--soluk:#5b6675;--cizgi:#dfe3e8;--ana:#1f4fd8;--ana-yazi:#fff;--vurgu:#eef4ff;--hata:#b42318;--hata-zemin:#fef3f2}
@media (prefers-color-scheme: dark){:root{--zemin:#12161c;--kart:#1a2028;--yazi:#e7ebf0;--soluk:#9aa6b4;--cizgi:#2c3541;--ana:#6f95ff;--ana-yazi:#0c1220;--vurgu:#1d2940;--hata:#ff8a80;--hata-zemin:#3a1d1b}}
*{box-sizing:border-box}
body{margin:0;background:var(--zemin);color:var(--yazi);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:1.6rem;margin:0 0 4px} h3{margin:8px 0} h4{margin:20px 0 6px}
.alt{color:var(--soluk);margin:0 0 20px}
.sekmeler{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.sekmeler button{flex:1;min-width:180px;padding:12px;border:1px solid var(--cizgi);background:var(--kart);color:var(--yazi);border-radius:10px;font:inherit;cursor:pointer}
.sekmeler button[aria-selected=true]{border-color:var(--ana);box-shadow:inset 0 0 0 1px var(--ana);font-weight:600}
.kart{background:var(--kart);border:1px solid var(--cizgi);border-radius:12px;padding:20px;margin-bottom:16px}
label{display:block;font-weight:600;margin:14px 0 4px}
label small,.ipucu{display:block;font-weight:400;color:var(--soluk);font-size:.9rem}
input[type=text],select{width:100%;padding:10px 12px;border:1px solid var(--cizgi);border-radius:8px;background:var(--kart);color:var(--yazi);font:inherit}
input[type=file]{width:100%;padding:10px;border:1px dashed var(--cizgi);border-radius:8px;font:inherit;color:var(--yazi)}
.iki{display:grid;grid-template-columns:1fr 1fr;gap:12px} @media (max-width:560px){.iki{grid-template-columns:1fr}}
details{margin-top:14px} summary{cursor:pointer;color:var(--ana);font-weight:600}
details .iki label{font-weight:400}
.gonder{margin-top:18px;padding:12px 20px;border:0;border-radius:8px;background:var(--ana);color:var(--ana-yazi);font:inherit;font-weight:600;cursor:pointer}
.gonder:disabled{opacity:.6;cursor:wait}
.dugmeler{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 4px}
.indir{display:inline-block;padding:10px 16px;border:1px solid var(--ana);border-radius:8px;color:var(--ana);background:transparent;font:inherit;font-weight:600;text-decoration:none;cursor:pointer}
.indir:disabled{opacity:.6;cursor:wait}
.bilgi{background:var(--vurgu);border-radius:8px;padding:10px 14px;margin:8px 0}
.bilgi a{color:var(--ana);font-weight:600}
.durum{font-weight:600} .adim{color:var(--soluk);font-size:.9rem;padding-left:20px} .adim li{margin:4px 0}
code{background:var(--vurgu);padding:1px 5px;border-radius:4px;font-size:.9em;word-break:break-all}
.ikincil{margin-top:18px;margin-left:8px;padding:12px 16px;border:1px solid var(--cizgi);border-radius:8px;background:transparent;color:var(--yazi);font:inherit;cursor:pointer}
.indir-not{color:var(--soluk);font-size:.9rem;margin:6px 0 12px}
.tablo{overflow-x:auto} table{border-collapse:collapse;width:100%;margin:6px 0}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--cizgi);white-space:nowrap}
th{font-size:.85rem;color:var(--soluk);font-weight:600}
tr.vurgu td{background:var(--vurgu);font-weight:600}
.sonuc{background:var(--vurgu);border-radius:8px;padding:12px 14px;margin:8px 0 14px}
.notlar{color:var(--soluk);font-size:.9rem;padding-left:18px} .notlar li{margin:4px 0}
.hata{background:var(--hata-zemin);color:var(--hata);border-radius:8px;padding:12px 14px}
hr{border:0;border-top:1px solid var(--cizgi);margin:24px 0}
footer{color:var(--soluk);font-size:.85rem;margin-top:24px}
[hidden]{display:none}
</style></head><body><main>
<h1>Pazar ve Komisyon Analizcisi</h1>
<p class="alt">Hesap bu bilgisayarda yapılır; girdiğiniz hiçbir bilgi internete gönderilmez.</p>

<div class="sekmeler" role="tablist">
  <button role="tab" aria-selected="true" data-sekme="komisyon">Komisyon karşılaştırması</button>
  <button role="tab" aria-selected="false" data-sekme="pazar">Pazar analizi</button>
</div>

<section class="kart" id="komisyon">
  <p class="ipucu">Ürününüzün kategorisini ve satış fiyatını girin; hangi pazaryerinde elinize ne kalacağını görün.</p>
  <form data-uc="/api/komisyon">
    <label>Kategori<select name="kategori" required><option value="">Seçin…</option>{{SECENEKLER}}</select></label>
    <div class="iki">
      <label>Satış fiyatı (TL)<input type="text" inputmode="decimal" name="fiyat" placeholder="ör. 899" required></label>
      <label>Ürün maliyeti (TL)<small>İsteğe bağlı; yazarsanız kârınız da hesaplanır.</small><input type="text" inputmode="decimal" name="maliyet" placeholder="ör. 400"></label>
    </div>
    <details><summary>Kendi komisyon oranlarım</summary>
      <p class="ipucu">Satıcı panelinizdeki sözleşme oranını yazarsanız tablodaki yaklaşık aralık yerine o kullanılır. Boş bıraktıklarınız için tablodaki değer geçerlidir.</p>
      <div class="iki">{{ORANLAR}}</div></details>
    <button class="gonder" type="submit">Hesapla</button>
  </form>
</section>

<section class="kart" id="pazar" hidden>
  <p class="ipucu">Bir ürün listesi yükleyin; fiyat bantlarını, öne çıkan markaları ve rekabet durumunu görün.</p>
  <form data-uc="/api/pazar">
    <label>Ürün listesi dosyası<small>CSV (Excel'den “CSV UTF-8” olarak kaydedilmiş), JSON ya da tarayıcıdan kaydedilmiş arama sayfası (HTML). CSV sütunları: ad, marka, fiyat, puan, yorum.</small>
      <input type="file" name="dosya" accept=".csv,.json,.html,.htm" required></label>
    <div class="iki">
      <label>Kategori<small>İsteğe bağlı; seçerseniz komisyon karşılaştırması da eklenir.</small><select name="kategori"><option value="">Seçmeyin ya da seçin…</option>{{SECENEKLER}}</select></label>
      <label>Ürün maliyeti (TL)<small>İsteğe bağlı.</small><input type="text" inputmode="decimal" name="maliyet" placeholder="ör. 150"></label>
    </div>
    <button class="gonder" type="submit">Analiz et</button>
  </form>
</section>

<section class="kart" id="cikti" hidden aria-live="polite"></section>

<section class="kart" id="sheets-karti">
  <details id="sheets-ayar">
    <summary>Google Sheets bağlantısı <span class="ipucu" style="display:inline;font-weight:400">— isteğe bağlı</span></summary>
    <p class="ipucu">Sonuçları kendi Google Sheets tablonuza göndermek isterseniz bir kez kurmanız yeterli. Kurmazsanız araç aynen çalışır; sonuçları Excel olarak indirebilirsiniz.</p>
    <p class="durum" id="sheets-durum">Durum denetleniyor…</p>
    <form id="sheets-form">
      <label>Google Sheets tablonuzun adresi<small>Tabloyu tarayıcıda açıp adres çubuğundaki adresi kopyalayın.</small>
        <input type="text" name="tablo" placeholder="https://docs.google.com/spreadsheets/d/…" required></label>
      <label>Hizmet hesabı anahtar dosyası<small>Google Cloud'dan indirdiğiniz .json dosyası. Bu bilgisayarda saklanır; başka hiçbir yere gönderilmez. Daha önce yüklediyseniz yeniden seçmeniz gerekmez.</small>
        <input type="file" name="anahtar" accept=".json,application/json"></label>
      <button class="gonder" type="submit">Kaydet ve bağlantıyı dene</button>
      <button class="ikincil" type="button" id="sheets-kaldir" hidden>Bağlantıyı kaldır</button>
    </form>
    <p class="ipucu" style="margin-top:14px">Kurulumda tablonuzu hizmet hesabının e-posta adresiyle <b>Düzenleyen</b> olarak paylaşmanız gerekir. Araç yalnızca Pazar, Komisyon ve Ürünler adlı sekmeleri yazar; tablonuzdaki diğer sekmelere dokunmaz.</p>
  </details>
</section>
<footer>Bu araç herhangi bir pazaryeriyle bağlantılı değildir. Sonuçlar bilgi amaçlıdır. Kapatmak için açılan siyah pencereyi kapatmanız yeterlidir.</footer>
</main>
<script>
const cikti = document.getElementById('cikti');
let sheets = {ayarli: false}, sonIstek = null;
const sheetsKarti = document.getElementById('sheets-ayar'), sheetsDurum = document.getElementById('sheets-durum');
async function gonderJson(uc, govde) {
  const yanit = await fetch(uc, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(govde)});
  return yanit.json();
}
function sheetsGoster(d) {
  sheets = d || {ayarli: false};
  sheetsDurum.textContent = '';
  if (sheets.ayarli) {
    sheetsDurum.append('Bağlı: ' + (sheets.tablo_adi || 'tablo') + ' — ');
    const b = document.createElement('a'); b.href = sheets.tablo; b.target = '_blank'; b.rel = 'noopener'; b.textContent = 'tabloyu aç';
    sheetsDurum.append(b);
    document.querySelector('#sheets-form [name=tablo]').value = sheets.tablo;
  } else if (sheets.hesap) {
    sheetsDurum.append('Anahtar yüklü, tablo henüz bağlanmadı. Tablonuzu şu adresle paylaşın: ');
    const k = document.createElement('code'); k.textContent = sheets.hesap; sheetsDurum.append(k);
  } else sheetsDurum.textContent = 'Henüz kurulmadı.';
  document.getElementById('sheets-kaldir').hidden = !sheets.hesap;
}
gonderJson('/api/sheets-durum', {}).then(sheetsGoster).catch(() => { sheetsDurum.textContent = 'Durum okunamadı.'; });
document.getElementById('sheets-form').addEventListener('submit', async olay => {
  olay.preventDefault();
  const form = olay.target, dugme = form.querySelector('.gonder'), eski = dugme.textContent;
  const govde = {tablo: form.tablo.value};
  try {
    const dosya = form.anahtar.files[0];
    if (dosya) { if (dosya.size > 100 * 1024) throw new Error('buyuk'); govde.anahtar_icerik = await dosya.text(); }
    dugme.disabled = true; dugme.textContent = 'Deneniyor…';
    const veri = await gonderJson('/api/sheets-ayar', govde);
    if (veri.hata) { sheetsDurum.textContent = veri.hata; sheetsDurum.className = 'hata'; return; }
    sheetsDurum.className = 'durum'; sheetsGoster(veri); form.anahtar.value = '';
  } catch (e) {
    sheetsDurum.className = 'hata';
    sheetsDurum.textContent = e.message === 'buyuk' ? 'Bu dosya bir anahtar dosyası için çok büyük.' : 'Program yanıt vermedi.';
  } finally { dugme.disabled = false; dugme.textContent = eski; }
});
document.getElementById('sheets-kaldir').addEventListener('click', async () => {
  sheetsDurum.className = 'durum'; sheetsGoster(await gonderJson('/api/sheets-kaldir', {}));
  document.querySelector('#sheets-form [name=tablo]').value = '';
});
async function sheetsGonder(dugme, mesaj) {
  if (!sheets.ayarli) {
    sheetsKarti.open = true; sheetsKarti.scrollIntoView({behavior: 'smooth', block: 'center'});
    mesaj.className = 'bilgi'; mesaj.textContent = 'Önce aşağıdaki “Google Sheets bağlantısı” bölümünden tablonuzu bağlayın.'; mesaj.hidden = false;
    return;
  }
  const eski = dugme.textContent; dugme.disabled = true; dugme.textContent = 'Gönderiliyor…'; mesaj.hidden = true;
  try {
    const veri = await gonderJson(sonIstek.uc, {...sonIstek.govde, sheets: true});
    mesaj.textContent = ''; mesaj.hidden = false;
    if (veri.hata) { mesaj.className = 'hata'; mesaj.textContent = veri.hata; return; }
    mesaj.className = 'bilgi';
    mesaj.append('Tablonuza yazıldı (' + veri.sheets.sekmeler.join(', ') + '). ');
    const b = document.createElement('a'); b.href = veri.sheets.adres; b.target = '_blank'; b.rel = 'noopener'; b.textContent = 'Tabloyu aç';
    mesaj.append(b);
    if (veri.sheets.hatali_hucre) mesaj.append(' Uyarı: ' + veri.sheets.hatali_hucre + ' hücre hata gösteriyor; tabloyu kontrol edin.');
  } catch (e) { mesaj.className = 'hata'; mesaj.textContent = 'Program yanıt vermedi.'; mesaj.hidden = false; }
  finally { dugme.disabled = false; dugme.textContent = eski; }
}
document.querySelectorAll('[data-sekme]').forEach(d => d.addEventListener('click', () => {
  document.querySelectorAll('[data-sekme]').forEach(x => x.setAttribute('aria-selected', x === d));
  for (const ad of ['komisyon', 'pazar']) document.getElementById(ad).hidden = ad !== d.dataset.sekme;
  cikti.hidden = true;
}));
function hataGoster(mesaj) {
  cikti.textContent = '';
  const p = document.createElement('p'); p.className = 'hata'; p.textContent = mesaj;
  cikti.appendChild(p); cikti.hidden = false;
}
document.querySelectorAll('form[data-uc]').forEach(form => form.addEventListener('submit', async olay => {
  olay.preventDefault();
  const dugme = form.querySelector('.gonder'); const eski = dugme.textContent;
  const govde = {kategori: form.kategori.value, maliyet: form.maliyet.value, oranlar: {}};
  document.querySelectorAll('[data-oran]').forEach(a => { if (a.value.trim()) govde.oranlar[a.dataset.oran] = a.value; });
  try {
    if (form.fiyat) govde.fiyat = form.fiyat.value;
    if (form.dosya) {
      const dosya = form.dosya.files[0];
      if (!dosya) return hataGoster('Lütfen bir dosya seçin.');
      if (dosya.size > 12 * 1024 * 1024) return hataGoster('Dosya çok büyük (en fazla 12 MB).');
      govde.dosya_adi = dosya.name; govde.icerik = await dosya.text();
    }
    dugme.disabled = true; dugme.textContent = 'Hesaplanıyor…';
    const veri = await gonderJson(form.dataset.uc, govde);
    if (veri.hata) return hataGoster(veri.hata);
    sonIstek = {uc: form.dataset.uc, govde};
    cikti.innerHTML = veri.html;
    if (veri.excel) {
      const ikili = Uint8Array.from(atob(veri.excel), k => k.charCodeAt(0));
      const baglanti = document.createElement('a');
      baglanti.href = URL.createObjectURL(new Blob([ikili], {type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
      baglanti.download = veri.excel_adi; baglanti.className = 'indir'; baglanti.textContent = 'Excel olarak indir';
      const aciklama = document.createElement('p'); aciklama.className = 'indir-not';
      aciklama.textContent = 'Excel dosyasında sarı hücreleri (fiyat, maliyet, oranlar) değiştirdiğinizde sonuçlar yeniden hesaplanır.';
      const tabloDugmesi = document.createElement('button');
      tabloDugmesi.type = 'button'; tabloDugmesi.className = 'indir'; tabloDugmesi.textContent = "Google Sheets'e gönder";
      const mesaj = document.createElement('p'); mesaj.hidden = true;
      tabloDugmesi.addEventListener('click', () => sheetsGonder(tabloDugmesi, mesaj));
      const sira = document.createElement('div'); sira.className = 'dugmeler'; sira.append(baglanti, tabloDugmesi);
      cikti.prepend(mesaj); cikti.prepend(aciklama); cikti.prepend(sira);
    }
    cikti.hidden = false; cikti.scrollIntoView({behavior: 'smooth', block: 'start'});
  } catch (e) {
    hataGoster('Program yanıt vermedi. Siyah pencere açık mı? Kapattıysanız Başlat dosyasına yeniden çift tıklayın.');
  } finally { dugme.disabled = false; dugme.textContent = eski; }
}));
</script></body></html>
"""


# ---------------------------------------------------------------- sunucu

class Istek(BaseHTTPRequestHandler):
    server_version = "PazarKomisyon"
    sys_version = ""

    def log_message(self, *_):  # terminali istek satırlarıyla doldurma
        pass

    def _yanit(self, kod: int, govde: bytes, tur: str) -> None:
        self.send_response(kod)
        self.send_header("Content-Type", tur)
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; "
                         "form-action 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(govde)

    def _json(self, kod: int, veri: dict) -> None:
        self._yanit(kod, json.dumps(veri, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _yerel_mi(self) -> bool:
        """Başka bir sitenin, tarayıcı üzerinden bu sunucuya istek atmasını engeller (DNS rebinding)."""
        ad = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if ad not in IZINLI_ADRESLER:
            return False
        kaynak = self.headers.get("Origin")
        if kaynak:
            sunucu = kaynak.split("://", 1)[-1].rsplit(":", 1)[0]
            return sunucu in IZINLI_ADRESLER
        return True

    def do_GET(self):
        if not self._yerel_mi():
            return self._yanit(403, b"Yalnizca bu bilgisayardan erisilebilir.", "text/plain; charset=utf-8")
        if self.path.split("?", 1)[0] == "/":
            return self._yanit(200, sayfa().encode("utf-8"), "text/html; charset=utf-8")
        self._yanit(404, b"Bulunamadi.", "text/plain; charset=utf-8")

    def do_POST(self):
        if not self._yerel_mi():
            return self._json(403, {"hata": "Yalnızca bu bilgisayardan erişilebilir."})
        islem = ISLEMLER.get(self.path)
        if islem is None:
            return self._json(404, {"hata": "Bulunamadı."})
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            return self._json(415, {"hata": "Beklenen içerik türü: application/json"})
        try:
            uzunluk = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            uzunluk = -1
        if uzunluk <= 0 or uzunluk > EN_BUYUK_ISTEK:
            return self._json(413, {"hata": "Dosya çok büyük ya da istek boş (en fazla 12 MB)."})
        try:
            girdi = json.loads(self.rfile.read(uzunluk).decode("utf-8"))
            if not isinstance(girdi, dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            return self._json(400, {"hata": "İstek okunamadı."})
        try:
            self._json(200, islem(girdi))
        except GirdiHatasi as hata:
            self._json(200, {"hata": str(hata)})
        except Exception:  # beklenmeyen hata: ayrıntı terminale, kullanıcıya sade mesaj
            import traceback
            traceback.print_exc()
            self._json(500, {"hata": "Beklenmeyen bir hata oluştu. Açılan siyah penceredeki mesajı proje sayfasına bildirebilirsiniz."})


def sunucu_kur(port: int = 8765) -> ThreadingHTTPServer:
    """127.0.0.1 üzerinde boş bir port bulur. Dışarıdan (ağdan) erişime açık DEĞİLDİR."""
    for aday in list(range(port, port + 20)) + [0]:
        try:
            return ThreadingHTTPServer(("127.0.0.1", aday), Istek)
        except OSError:
            continue
    raise OSError("Boş port bulunamadı.")


def main() -> int:
    # Türkçe olmayan Windows konsollarında "ş, ı" gibi harfler yazdırılamayıp programı durdurmasın.
    for akis in (sys.stdout, sys.stderr):
        if hasattr(akis, "reconfigure"):
            akis.reconfigure(errors="replace")
    sunucu = sunucu_kur()
    adres = f"http://127.0.0.1:{sunucu.server_address[1]}/"
    print("=" * 62)
    print("  Pazar ve Komisyon Analizcisi çalışıyor.")
    print(f"  Tarayıcınızda açılmadıysa şu adresi yazın: {adres}")
    print("  Kapatmak için bu pencereyi kapatın (ya da Ctrl+C).")
    print("=" * 62)
    threading.Timer(0.6, lambda: webbrowser.open(adres)).start()
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nKapatıldı.")
    finally:
        sunucu.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
