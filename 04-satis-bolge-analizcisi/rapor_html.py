"""Sonucu tek dosyalık, tarayıcıda açılan ve yazdırılabilen bir rapor sayfasına (HTML) çevirir.

Yalnızca standart kütüphane kullanılır. Sayfaya yazılan her metin kaçışlanır; listedeki bir il, ilçe, mahalle
ya da ürün adı sayfaya kod olarak giremez. Sayfa internete bağlanmaz, dış dosya yüklemez.
"""

from __future__ import annotations

from datetime import date
from html import escape

from analiz import MAHALLE_EN_AZ, ORAN_EN_AZ, Rapor, Satir

AYLAR = ("Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık")
IL_AYRINTI = 8  # ilçe ve mahalle ayrıntısı verilen il sayısı

STIL = """
*{box-sizing:border-box}body{margin:0;background:#F3EEE4;color:#2B2B2B;font:16px/1.5 -apple-system,"Segoe UI",Arial,sans-serif}
main{max-width:980px;margin:0 auto;padding:40px 24px 60px}h1{font-size:34px;line-height:1.15;margin:6px 0 8px}
h2{font-size:22px;margin:44px 0 6px}h3{font-size:18px;margin:0 0 2px}.etiket{font-size:12px;font-weight:700;letter-spacing:.06em;color:#6F6C66}
.alt{color:#6F6C66;margin:0 0 14px}.kutular{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0 0}
.kutu{background:#E6E4DF;border-radius:14px;padding:16px 18px}.kutu b{display:block;font-size:28px;line-height:1.1}
.kutu span{font-size:14px;color:#6F6C66}.oneri{background:#E6E4DF;border-radius:14px;padding:18px 20px;margin:12px 0;break-inside:avoid}
.oneri .tur{display:inline-block;background:#C4532D;color:#F3EEE4;font-size:12px;font-weight:700;border-radius:999px;padding:2px 10px;margin-right:8px}
.oneri p{margin:8px 0 0}.oneri .yap{border-left:3px solid #C4532D;padding-left:12px}
table{width:100%;border-collapse:collapse;margin:8px 0 0;font-size:15px}th{text-align:left;font-size:13px;color:#6F6C66;font-weight:700;padding:8px 10px;border-bottom:1px solid #CFCBC2}
td{padding:8px 10px;border-bottom:1px solid #DDD9D0;vertical-align:top}.sag{text-align:right;white-space:nowrap}
.cubuk{display:inline-block;height:10px;border-radius:5px;background:#2B2B2B;vertical-align:middle;margin-right:8px}
.cubuk.v{background:#C4532D}.il{background:#E6E4DF;border-radius:14px;padding:18px 20px;margin:14px 0;break-inside:avoid}
.il .ust{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}.il .ust span{color:#6F6C66;font-size:14px}
.mah{color:#6F6C66;font-size:14px;margin-top:3px}.mah b{color:#2B2B2B;font-weight:600}.not{font-size:14px;color:#6F6C66}
.yuksek{color:#C4532D;font-weight:700}footer{margin-top:44px;font-size:13px;color:#6F6C66;border-top:1px solid #CFCBC2;padding-top:14px}
@media(max-width:700px){.kutular{grid-template-columns:repeat(2,1fr)}h1{font-size:27px}table{font-size:14px}}
@media print{body{background:#fff}main{padding:0}.kutu,.oneri,.il{border:1px solid #CFCBC2}}
"""


def e(metin) -> str:
    return escape(str(metin), quote=True)


def yz(x: float | None) -> str:
    return "" if x is None else "%" + f"{x:.1f}".replace(".", ",")


def tl(x: float | None) -> str:
    return "" if x is None else f"{x:,.0f}".replace(",", ".") + " TL"


def _cubuk(deger: float, en_buyuk: float, vurgu: bool = False, genislik: int = 120) -> str:
    px = max(3, round(genislik * deger / en_buyuk)) if en_buyuk else 3
    return f'<span class="cubuk{" v" if vurgu else ""}" style="width:{px}px"></span>'


def _tablo(basliklar: list[tuple[str, bool]], satirlar: list[list[tuple[str, bool]]]) -> str:
    """Hücreler (hazır HTML, sağa yaslı mı) çiftleridir; metinler çağıran tarafta kaçışlanır."""
    bas = "".join(f'<th{" class=sag" if sag else ""}>{e(ad)}</th>' for ad, sag in basliklar)
    govde = "".join("<tr>" + "".join(f'<td{" class=sag" if sag else ""}>{h}</td>' for h, sag in s) + "</tr>" for s in satirlar)
    return f"<table><thead><tr>{bas}</tr></thead><tbody>{govde}</tbody></table>"


def _iade_hucre(x: Satir, r: Rapor) -> tuple[str, bool]:
    if x.iade_orani is None:
        return ("", True)
    yuksek = r.iade_orani is not None and x.siparis >= ORAN_EN_AZ and x.iade >= 3 and x.iade_orani >= max(r.iade_orani * 1.5, r.iade_orani + 3)
    return (f'<span class="yuksek">{yz(x.iade_orani)}</span>' if yuksek else yz(x.iade_orani), True)


def _dagilim(ad: str, satirlar: list[Satir], r: Rapor, urun: bool = False) -> str:
    en_buyuk = max((x.siparis for x in satirlar), default=1)
    bas = [(ad, False), ("Sipariş", False), ("Pay", True)]
    if r.ciro is not None:
        bas += [("Ciro", True), ("Ort. sepet", True)]
    if r.iade_bilgisi_var:
        bas += [("İade", True)]
    if urun and r.urun_bilgisi_var:
        bas += [("En çok satan ürün", False)]
    govde = []
    for x in satirlar:
        s = [(f"<b>{e(x.ad)}</b>", False), (_cubuk(x.siparis, en_buyuk) + e(x.siparis), False), (yz(x.pay), True)]
        if r.ciro is not None:
            s += [(tl(x.ciro), True), (tl(x.ortalama_sepet), True)]
        if r.iade_bilgisi_var:
            s += [_iade_hucre(x, r)]
        if urun and r.urun_bilgisi_var:
            s += [(e(x.en_cok_satan), False)]
        govde.append(s)
    return _tablo(bas, govde)


def _il_karti(il: Satir, r: Rapor) -> str:
    ilceler = r.il_ilceleri.get(il.ad, [])
    ust = (f'<div class="ust"><h3>{e(il.ad)}</h3><span>{e(il.siparis)} sipariş · payı {yz(il.pay)}'
           + (f" · ortalama sepet {tl(il.ortalama_sepet)}" if il.ortalama_sepet is not None else "")
           + (f" · iade {yz(il.iade_orani)}" if il.iade_orani is not None else "") + "</span></div>")
    if not ilceler:
        return f'<div class="il">{ust}<p class="not">Bu ilde ilçe bilgisi yok.</p></div>'
    en_buyuk = ilceler[0].siparis
    bas = [("İlçe ve mahalleleri", False), ("Sipariş", False), ("İldeki payı", True)]
    if r.ciro is not None:
        bas += [("Ort. sepet", True)]
    if r.iade_bilgisi_var:
        bas += [("İade", True)]
    govde = []
    for x in ilceler:
        mahalleler = r.ilce_mahalleleri.get(f"{il.ad} / {x.ad}", [])
        mah = ('<div class="mah">' + " · ".join(f"<b>{e(m.ad)}</b> {e(m.siparis)}" for m in mahalleler[:6]) + "</div>") if mahalleler else ""
        s = [(f"<b>{e(x.ad)}</b>{mah}", False), (_cubuk(x.siparis, en_buyuk, vurgu=True) + e(x.siparis), False),
             (yz(100 * x.siparis / il.siparis), True)]
        if r.ciro is not None:
            s += [(tl(x.ortalama_sepet), True)]
        if r.iade_bilgisi_var:
            s += [_iade_hucre(x, r)]
        govde.append(s)
    return f'<div class="il">{ust}{_tablo(bas, govde)}</div>'


def sayfa(r: Rapor, bugun: date, baslik: str = "") -> str:
    tarih = f"{bugun.day} {AYLAR[bugun.month - 1]} {bugun.year}"
    ad = baslik.strip() or "Satış bölge raporu"
    kutular = [(f"{r.siparis_sayisi:,}".replace(",", "."), "sipariş"), (str(r.il_sayisi), "ile satış var (81 il içinde)"),
               (yz(r.ilk3_pay), "ilk üç ilin sipariş payı")]
    kutular.insert(1, (tl(r.ciro), "ciro") if r.ciro is not None else (str(len(r.siparis_gelmeyen_iller)), "ile hiç satış yok"))
    p = [f"<!doctype html><html lang=tr><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
         f"<title>{e(ad)}</title><style>{STIL}</style></head><body><main>",
         f'<div class="etiket">SATIŞ BÖLGE ANALİZCİSİ · {e(tarih)}</div><h1>{e(ad)}</h1>',
         '<p class="alt">Sipariş listenizden çıkarılan il, ilçe ve mahalle dağılımı; sayılara dayanan bulgular ve öneriler.</p>',
         '<div class="kutular">' + "".join(f'<div class="kutu"><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in kutular) + "</div>"]

    p.append("<h2>Bulgular ve öneriler</h2>")
    if r.oneriler:
        p.append('<p class="alt">Her bulgu listedeki bir sayıya dayanır. Öneriler deneyebileceğiniz adımlardır; kesin sonuç sözü değildir.</p>')
        for o in r.oneriler:
            p.append(f'<div class="oneri"><span class="tur">{e(o.tur)}</span><b>{e(o.baslik)}</b>'
                     f'<p>{e(o.bulgu)}</p><p class="yap"><b>Öneri:</b> {e(o.oneri)}</p></div>')
    else:
        p.append('<p class="alt">Bu listede kural eşiklerini aşan bir bulgu çıkmadı; dağılım tabloları aşağıdadır.</p>')

    p.append("<h2>Bölgeler</h2>" + _dagilim("Bölge", r.bolgeler, r))
    p.append("<h2>İller</h2>" + f'<p class="alt">Sipariş gelen {r.il_sayisi} ilin tamamı.</p>' + _dagilim("İl", r.iller, r, urun=True))

    if r.il_ilceleri:
        p.append("<h2>İl il, ilçe ilçe" + (", mahalle mahalle" if r.mahalle_bilgisi_var else "") + "</h2>")
        p.append(f'<p class="alt">En çok sipariş gelen {min(IL_AYRINTI, len(r.iller))} ilin ilçeleri'
                 + (f"; her ilçenin altında en az {MAHALLE_EN_AZ} sipariş gelen mahalleleri." if r.mahalle_bilgisi_var else ".") + "</p>")
        p += [_il_karti(il, r) for il in r.iller[:IL_AYRINTI]]
    if r.mahalleler:
        en_buyuk = r.mahalleler[0].siparis
        govde = []
        for x in r.mahalleler[:20]:
            il, ilce, mah = x.ad.split(" / ")
            s = [(f"<b>{e(mah)}</b>", False), (e(f"{ilce}, {il}"), False), (_cubuk(x.siparis, en_buyuk, vurgu=True) + e(x.siparis), False)]
            if r.ciro is not None:
                s += [(tl(x.ortalama_sepet), True)]
            govde.append(s)
        p.append("<h2>En çok sipariş gelen mahalleler</h2>"
                 + _tablo([("Mahalle", False), ("İlçe, il", False), ("Sipariş", False)] + ([("Ort. sepet", True)] if r.ciro is not None else []), govde))
    elif not r.mahalle_bilgisi_var:
        p.append('<p class="not">Listede mahalle sütunu olmadığı için mahalle dağılımı çıkarılmadı.</p>')

    if r.siparis_gelmeyen_iller:
        p.append(f"<h2>Sipariş gelmeyen iller ({len(r.siparis_gelmeyen_iller)})</h2><p>{e(', '.join(r.siparis_gelmeyen_iller))}</p>")

    p.append("<h2>Yöntem ve sınırlar</h2><ul class=not>")
    notlar = ["Rapor yalnızca verilen sipariş listesini kapsar; iptal edilen siparişler ve ili tanınmayan satırlar sayılmaz."
              + (f" Bu listede {r.iptal} iptal satırı vardı." if r.iptal else ""),
              "İl, ilçe ve mahalle listedeki sütunlardan olduğu gibi alınır; müşteri adı, telefon ve açık adres kullanılmaz.",
              f"{MAHALLE_EN_AZ} siparişten azı olan mahalleler tek tek gösterilmez."
              + (f" Bu listede {r.kucuk_mahalle} mahalle bu yüzden gösterilmedi." if r.kucuk_mahalle else ""),
              f"İade oranı ve ortalama sepet yalnızca en az {ORAN_EN_AZ} siparişi olan yerlerde yorumlanır; az siparişte oranlar yanıltır.",
              "Öneriler sabit kurallarla üretilir: nüfus, mevsim, reklam geçmişi ve kâr hesaba katılmaz. Bir ilin payının yüksek "
              "olması nüfusla da ilgilidir.",
              "Araç herhangi bir pazaryeriyle bağlantılı değildir; rapor bilgi amaçlıdır."]
    p.append("".join(f"<li>{e(n)}</li>" for n in notlar + r.uyarilar) + "</ul>")
    p.append("<footer>Satış Bölge Analizcisi · Harun Gökce · github.com/Harungokc/eticaret-agentlari</footer></main></body></html>")
    return "".join(p)
