"""Sonucu tek dosyalık, tarayıcıda açılan ve yazdırılabilen bir rapor sayfasına (HTML) çevirir.

Yalnızca standart kütüphane kullanılır. Sayfaya yazılan her metin kaçışlanır; raporda geçen bir ürün, kampanya ya da
arama terimi sayfaya kod olarak giremez. Sayfa internete bağlanmaz, dış dosya yüklemez.
"""

from __future__ import annotations

from datetime import date
from html import escape

from analiz import EN_AZ_GOSTERIM, EN_AZ_SIPARIS, EN_AZ_TIKLAMA, Kalem, Rapor

AYLAR = ("Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık")

STIL = """
*{box-sizing:border-box}body{margin:0;background:#F3EEE4;color:#2B2B2B;font:16px/1.5 -apple-system,"Segoe UI",Arial,sans-serif}
main{max-width:980px;margin:0 auto;padding:40px 24px 60px}h1{font-size:34px;line-height:1.15;margin:6px 0 8px}
h2{font-size:22px;margin:44px 0 6px}.etiket{font-size:12px;font-weight:700;letter-spacing:.06em;color:#6F6C66}
.alt{color:#6F6C66;margin:0 0 14px}.kutular{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0 0}
.kutu{background:#E6E4DF;border-radius:14px;padding:16px 18px}.kutu b{display:block;font-size:28px;line-height:1.1}
.kutu span{font-size:14px;color:#6F6C66}.oneri{background:#E6E4DF;border-radius:14px;padding:18px 20px;margin:12px 0;break-inside:avoid}
.oneri .tur{display:inline-block;background:#C4532D;color:#F3EEE4;font-size:12px;font-weight:700;border-radius:999px;padding:2px 10px;margin-right:8px}
.oneri p{margin:8px 0 0}.oneri .yap{border-left:3px solid #C4532D;padding-left:12px}
.kaydir{overflow-x:auto}table{width:100%;border-collapse:collapse;margin:8px 0 0;font-size:14px}
th{text-align:left;font-size:12px;color:#6F6C66;font-weight:700;padding:8px 7px;border-bottom:1px solid #CFCBC2}
td{padding:8px 7px;border-bottom:1px solid #DDD9D0;vertical-align:top;white-space:nowrap}td:first-child{white-space:normal;min-width:170px}.sag{text-align:right;white-space:nowrap}
.not{font-size:14px;color:#6F6C66}.kotu{color:#C4532D;font-weight:700}
footer{margin-top:44px;font-size:13px;color:#6F6C66;border-top:1px solid #CFCBC2;padding-top:14px}
@media(max-width:700px){.kutular{grid-template-columns:repeat(2,1fr)}h1{font-size:27px}table{font-size:14px}}
@media print{body{background:#fff}main{padding:0}.kutu,.oneri{border:1px solid #CFCBC2}}
"""


def e(metin) -> str:
    return escape(str(metin), quote=True)


def yz(x: float | None) -> str:
    return "" if x is None else "%" + f"{x:.1f}".replace(".", ",")


def tl(x: float | None) -> str:
    return "" if x is None else f"{x:,.0f}".replace(",", ".") + " TL"


def sy(x: float | None) -> str:
    return "" if x is None else f"{x:,.0f}".replace(",", ".")


def kat(x: float | None) -> str:
    return "" if x is None else f"{x:.1f}".replace(".", ",")


def _tablo(kalemler: list[Kalem], r: Rapor, ad: str, kar: bool, sinir: int = 40) -> str:
    bas = [(ad, False), ("Harcama", True), ("Satış", True), ("ROAS", True), ("Maliyet oranı", True), ("Sipariş", True),
           ("Tıklama", True), ("Dönüşüm", True)]
    if kar:
        bas += [("Başa baş", True), ("Reklam sonrası", True)]
    bas += [("Durum", False)]
    govde = []
    for k in kalemler[:sinir]:
        kotu = k.durum in ("Satış yok", "Zarar", "Reklamsız da zarar")
        h = [(f"<b>{e(k.ad)}</b>" + (f'<div class="not">{e(k.kampanya)}</div>' if k.kampanya and ad != "Kampanya" else ""), False),
             (e(tl(k.harcama)), True), (e(tl(k.ciro)), True), (e(kat(k.roas)), True),
             (e(yz(k.acos)), True), (e(sy(k.siparis)), True), (e(sy(k.tiklama)), True), (e(yz(k.cvr)), True)]
        if kar:
            h += [(e(yz(k.basa_bas_acos)), True), (f'<span class="{"kotu" if (k.net or 0) < 0 else ""}">{e(tl(k.net))}</span>', True)]
        h += [(f'<span class="{"kotu" if kotu else ""}">{e(k.durum)}</span>', False)]
        govde.append(h)
    ust = "".join(f'<th{" class=sag" if sag else ""}>{e(a)}</th>' for a, sag in bas)
    satirlar = "".join("<tr>" + "".join(f'<td{" class=sag" if sag else ""}>{x}</td>' for x, sag in s) + "</tr>" for s in govde)
    ek = f'<p class="not">İlk {sinir} kalem gösterildi; tamamı Excel dosyasında.</p>' if len(kalemler) > sinir else ""
    return f'<div class="kaydir"><table><thead><tr>{ust}</tr></thead><tbody>{satirlar}</tbody></table></div>{ek}'


def sayfa(r: Rapor, bugun: date, baslik: str = "") -> str:
    tarih = f"{bugun.day} {AYLAR[bugun.month - 1]} {bugun.year}"
    ad = baslik.strip() or "Reklam raporu"
    kutular = [(tl(r.harcama), "reklam harcaması"), (tl(r.ciro) if r.ciro is not None else "—", "reklamdan gelen satış"),
               (kat(r.roas) if r.roas is not None else "—", "reklam getirisi (ROAS)")]
    if r.maliyet_var and r.net is not None:
        kutular.append((tl(r.net), "reklam sonrası kalan"))
    else:
        kutular.append((tl(r.satis_getirmeyen_harcama), "satış getirmeyen harcama"))
    p = [f"<!doctype html><html lang=tr><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
         f"<title>{e(ad)}</title><style>{STIL}</style></head><body><main>",
         f'<div class="etiket">REKLAM ANALİZCİSİ · {e(tarih)}</div><h1>{e(ad)}</h1>',
         '<p class="alt">Reklam raporunuzdan çıkarılan harcama, satış ve kâr tablosu; sayılara dayanan bulgular ve öneriler.</p>',
         '<div class="kutular">' + "".join(f'<div class="kutu"><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in kutular) + "</div>"]

    p.append("<h2>Bulgular ve öneriler</h2>")
    if r.oneriler:
        p.append('<p class="alt">Her bulgu rapordaki bir sayıya dayanır. Öneriler deneyebileceğiniz adımlardır; kesin sonuç sözü değildir.</p>')
        for o in r.oneriler:
            p.append(f'<div class="oneri"><span class="tur">{e(o.tur)}</span><b>{e(o.baslik)}</b>'
                     f'<p>{e(o.bulgu)}</p><p class="yap"><b>Öneri:</b> {e(o.oneri)}</p></div>')
    else:
        p.append('<p class="alt">Bu raporda kural eşiklerini aşan bir bulgu çıkmadı; tablolar aşağıdadır.</p>')

    if r.kalemler:
        p.append(f"<h2>{'Ürünler' if r.birim == 'Ürün' else 'Kampanyalar'}</h2>"
                 '<p class="alt">Harcamaya göre sıralı. ROAS: satış ÷ harcama. Maliyet oranı: harcama ÷ satış.'
                 + (" Başa baş: maliyet oranı bunun üstündeyse reklam zarar ettirir." if r.maliyet_var else "") + "</p>")
        p.append(_tablo(r.kalemler, r, r.birim, kar=r.maliyet_var))
    if r.terimler:
        p.append("<h2>Arama terimleri</h2>" + _tablo(r.terimler, r, "Arama terimi", kar=False))

    p.append("<h2>Yöntem ve sınırlar</h2><ul class=not>")
    notlar = ["Rapor yalnızca verilen reklam raporunu kapsar. Satış ve sipariş, pazaryerinin reklama bağladığı rakamlardır.",
              "Panelin gösterdiği reklam satışı, reklam olmasa da gelecek satışları ayırmaz. Özellikle markanızın adıyla "
              "aranan reklamlarda reklam getirisi gerçek etkiden yüksek görünebilir.",
              f"\"Satış yok\": en az {EN_AZ_TIKLAMA} tıklama alıp satış getirmeyen kalem. Kârlılık ve oranlar en az "
              f"{EN_AZ_SIPARIS} siparişi olan kalemde yorumlanır; tıklama oranı en az {EN_AZ_GOSTERIM} gösterimde.",
              "Öneriler sabit kurallarla üretilir; mevsim, stok, rakip ve reklam ayarlarınız hesaba katılmaz."]
    if r.maliyet_var:
        notlar.append("Sipariş başına kâr = satış fiyatı − ürün maliyeti − komisyon − kargo"
                      + (f"; maliyet dosyası olmayan ürünlerde genel kâr payı (%{kat(r.kar_marji)}) kullanıldı." if r.kar_marji else ".")
                      + " Satış fiyatı verilmediyse reklamdan gelen satış ÷ sipariş alınır.")
    p.append("".join(f"<li>{e(n)}</li>" for n in notlar + r.uyarilar) + "</ul>")
    p.append("<footer>Reklam Analizcisi · Harun Gökce · github.com/Harungokc/eticaret-agentlari</footer></main></body></html>")
    return "".join(p)
