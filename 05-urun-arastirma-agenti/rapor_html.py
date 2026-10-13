"""Değerlendirme sonucunu tek dosyalık, yazdırılabilir bir rapor sayfasına (HTML) çevirir.

Ek paket ve betik (JavaScript) kullanılmaz. Listeden gelen her metin kaçışlanarak yazılır; ürün adına ya da
nota yazılmış bir kod sayfada çalışmaz. Bağlantılar yalnızca http ve https adreslerine verilir.
"""

from __future__ import annotations

import re
from datetime import date
from html import escape

from analiz import (ARTIS_TABAN, AyTarihi, AZ_SATICI, guvenli_adres, inceleme_baglantilari, ESIK_SATIS, ESIK_YUKSELIS, IVME_TABAN, ORTA_SATICI, RISK_ETIKETI, YENI_GUN, Degerlendirme, Puan, adaylar,
                    adet_yaz, alan_adi, bilgi_girilenler, cok_satanlar, derinlesti, digerleri, guncel_ozet, iki_listede, kaynak_ciftleri,
                    TEDARIK_NOTU, tedarik_gruplari, tedarik_sayilari, tl, yukselenler, yuzde_yaz)

KART_SAYISI = 12  # yükselenlerin ilk bu kadarı ayrıntılı kart olarak, kalanı tablo olarak gösterilir
AYLAR = ("Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık")

_STIL = """
:root{--fon:#F3EEE4;--kutu:#E6E4DF;--yazi:#2B2B2B;--soluk:#5F5C57;--cizgi:#CFCCC5}
*{box-sizing:border-box}
body{margin:0;background:var(--fon);color:var(--yazi);font:16px/1.55 Arial,Helvetica,sans-serif}
main{max-width:860px;margin:0 auto;padding:40px 20px 56px}
h1{font-size:30px;line-height:1.2;margin:6px 0 10px}
h2{font-size:21px;margin:44px 0 6px;padding-top:18px;border-top:1px solid var(--cizgi)}
h3{font-size:17px;margin:0}
p{margin:8px 0}
a{color:inherit}
.ust{font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:var(--soluk)}
.soluk{color:var(--soluk);font-size:14px}
.sayilar{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0}
.sayi{flex:1 1 150px;background:var(--kutu);padding:14px 16px}
.sayi b{display:block;font-size:30px;line-height:1.1}
.kart{background:var(--kutu);padding:18px 20px;margin:14px 0;break-inside:avoid}
.bas{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px 14px;align-items:baseline}
.etiket{font-size:12px;letter-spacing:.06em;text-transform:uppercase;border:1px solid var(--yazi);padding:2px 8px;white-space:nowrap}
.puanlar{display:flex;flex-wrap:wrap;gap:8px 28px;margin:12px 0 6px}
.puan{flex:1 1 240px}
.puan span{display:flex;justify-content:space-between;font-size:14px}
.cubuk{height:8px;background:var(--cizgi);margin-top:4px}
.cubuk i{display:block;height:8px;background:var(--yazi)}
ul{margin:6px 0;padding-left:20px}
li{margin:3px 0}
.incele{font-size:14px;line-height:1.7;margin:8px 0}
.gorsel{width:104px;height:104px;object-fit:contain;background:#fff;flex:0 0 auto}
.kucuk{width:56px;height:56px;object-fit:contain;background:#fff;float:left;margin:0 10px 6px 0}
.ustkisim{display:flex;gap:16px;align-items:flex-start}
.ustkisim>div{flex:1 1 auto;min-width:0}
.uyari{border-left:3px solid var(--yazi);padding:2px 0 2px 12px;margin:10px 0;font-size:15px}
.tablo{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px;margin:10px 0}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--cizgi)}
th{font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--soluk);font-weight:normal}
td.r,th.r{text-align:right;white-space:nowrap}
td:first-child{min-width:190px}
td.bos{height:34px}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--cizgi);font-size:13px;color:var(--soluk)}
@media print{body{background:#fff}main{padding:0}h2{break-after:avoid}}
"""


def tarih_yaz(t: date) -> str:
    return f"{AYLAR[t.month - 1]} {t.year}" if isinstance(t, AyTarihi) else f"{t.day} {AYLAR[t.month - 1]} {t.year}"


def _a(etiket: str, adres: str) -> str:
    return f'<a href="{escape(adres, quote=True)}" target="_blank" rel="noopener noreferrer nofollow">{escape(etiket)}</a>'


def _b(kaynak: str) -> str:
    """Kaynağı bağlantı olarak yazar; http/https dışındaki adresler düz metin kalır."""
    ad, adres = alan_adi(kaynak) or kaynak, guvenli_adres(kaynak)
    return escape(ad) if adres is None else _a(ad, adres)


def _gorsel(d: Degerlendirme, sinif: str = "gorsel") -> str:
    """Ürün fotoğrafı; yalnızca https adresi kabul edilir. Fotoğraf kaynağın sunucusundan yüklenir."""
    adres = d.aday.gorsel.strip()
    if not re.match(r"https://[^\s\"'<>]+$", adres, re.I):
        return ""
    return (f'<img class="{sinif}" src="{escape(adres, quote=True)}" alt="{escape(d.aday.ad, quote=True)}" '
            'loading="lazy" referrerpolicy="no-referrer">')


def _kimlik(d: Degerlendirme) -> str:
    """Ürünün kaynaktaki adı, markası ve fiyatı: satıcı hangi ürüne baktığını bilsin."""
    a = d.aday
    parcalar = ([f"Listedeki adı: {a.orijinal_ad}"] if a.orijinal_ad else []) + ([f"Marka: {a.marka}"] if a.marka else []) \
        + ([f"Yurt dışı fiyatı: {a.yurtdisi_fiyat}"] if a.yurtdisi_fiyat else []) \
        + ([f"Çin'de fabrika fiyatı (liste): {a.tedarik_fiyat}" + (f", en az {a.tedarik_moq} adet" if a.tedarik_moq else "")
            + (f" ({a.tedarikci})" if a.tedarikci else "")] if a.tedarik_fiyat else []) + ([f"Çince adı: {a.cince_ad}"] if a.cince_ad else [])
    return f'<div class="soluk">{escape(" · ".join(parcalar))}</div>' if parcalar else ""


def _incele(d: Degerlendirme, gruplar: tuple[str, ...] = ("Ürünü gör", "Çin'de tedarik", "Türkiye'de bak")) -> str:
    satirlar = []
    for grup, baglantilar in inceleme_baglantilari(d.aday).items():
        if grup in gruplar and baglantilar:
            satirlar.append(f"<b>{escape(grup)}:</b> " + " · ".join(_a(e, adres) for e, adres in baglantilar))
    return '<div class="incele">' + "<br>".join(satirlar) + "</div>" if satirlar else ""


def _cubuk(ad: str, p: Puan) -> str:
    if p.puan is None:
        return f'<div class="puan"><span><b>{ad}</b><span>ölçülemedi</span></span><div class="cubuk"></div></div>'
    return (f'<div class="puan"><span><b>{ad}</b><span>{p.puan} / 100 · kanıt {p.kanit}</span></span>'
            f'<div class="cubuk"><i style="width:{p.puan}%"></i></div></div>')


def _kaynaklar(d: Degerlendirme) -> str:
    """Kaynak bağlantıları; aynı sitenin birden çok sayfası "site [2]" diye numaralanır."""
    parcalar, sayac = [], {}
    for k, t in kaynak_ciftleri(d.aday):
        alan = alan_adi(k) or k
        sayac[alan] = sayac.get(alan, 0) + 1
        adres = guvenli_adres(k)
        etiket = alan if sayac[alan] == 1 else f"{alan} [{sayac[alan]}]"
        parcalar.append((escape(etiket) if adres is None else _a(etiket, adres)) + (f" ({tarih_yaz(t)})" if t else ""))
    return ", ".join(parcalar) or "kaynak bağlantısı yok"


def _kart(d: Degerlendirme) -> str:
    a = d.aday
    alt = " · ".join(escape(x) for x in (a.kategori, a.ulke, f"veri tarihi {tarih_yaz(a.veri_tarihi)}" if a.veri_tarihi else "") if x)
    p = ['<div class="kart"><div class="ustkisim">', _gorsel(d), "<div>",
         f'<div class="bas"><h3>{escape(a.ad)}</h3><span class="etiket">{escape(d.sinif)}</span></div>']
    if alt:
        p.append(f'<div class="soluk">{alt}</div>')
    p.append(_kimlik(d))
    p.append("</div></div>")
    p.append(f'<div class="puanlar">{_cubuk("Yükseliş", d.yukselis)}{_cubuk("Satış gücü", d.satis)}</div>')
    p.append(f"<p>{escape(d.sinif_gerekce)}</p>")
    rakamlar = d.yukselis.aciklamalar + d.satis.aciklamalar + ([f"Video izlenmesi: {adet_yaz(a.izlenme)}."] if a.izlenme else [])
    if rakamlar:
        p.append("<ul>" + "".join(f"<li>{escape(r)}</li>" for r in rakamlar) + "</ul>")
    eksik = d.yukselis.eksikler + d.satis.eksikler
    if eksik:
        p.append(f'<p class="soluk">Görülemeyen: {escape(", ".join(eksik))}.</p>')
    for r in d.riskler:
        p.append(f'<div class="uyari"><b>{RISK_ETIKETI[r.duzey]}</b> · {escape(r.mesaj)}</div>')
    if a.aciklama:
        p.append(f'<p class="soluk">Not: {escape(a.aciklama)}</p>')
    p.append(_incele(d))
    p.append(f'<p class="soluk">Rakamların kaynağı: {_kaynaklar(d)}</p></div>')
    return "".join(p)


def _puan(p: Puan) -> str:
    return "–" if p.puan is None else str(p.puan)


def _tablo(basliklar: list[str], satirlar: list[list[str]], sag: tuple[int, ...] = ()) -> str:
    """Hücreler önceden kaçışlanmış HTML olarak verilir."""
    th = "".join(f'<th{" class=r" if i in sag else ""}>{b}</th>' for i, b in enumerate(basliklar))
    tr = "".join("<tr>" + "".join(f'<td{" class=r" if i in sag else ""}>{h}</td>' for i, h in enumerate(s)) + "</tr>" for s in satirlar)
    return f'<div class="tablo"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def _uyari(d: Degerlendirme) -> str:
    return f'<br><span class="soluk">Uyarı: {escape(", ".join(r.konu.lower() for r in d.riskler))}</span>' if d.riskler else ""


def _tedarik(sonuc: list[Degerlendirme], fiyatli: int, cinceli: int) -> str:
    """Çin'de tedarik bölümü: ürün türü başına Çince ad, fabrika liste fiyatı, en az sipariş ve arama bağlantıları."""
    p = ["<h2>Çin'de tedarik</h2>"]
    gruplar = tedarik_gruplari(sonuc)
    if not gruplar:
        p.append("<p>Bu taramada Çin'deki fabrika fiyatı ve Çince ürün adı toplanmadı. Her ürünün altındaki “Çin'de tedarik” "
                 "bağlantılarıyla Alibaba, AliExpress, Made-in-China ve Temu'da ürünün adıyla arama açabilirsiniz.</p>")
        return "".join(p)
    p.append(f'<p class="soluk">Ürün türü başına Çin’deki üretici dizininde görülen liste fiyatı. {len(sonuc)} ürünün {fiyatli} tanesinde '
             f"fabrika fiyatı, {cinceli} tanesinde 1688 ve Taobao araması için Çince ad var. {escape(TEDARIK_NOTU)} "
             "1688, Taobao ve benzeri Çin siteleri otomatik okunamaz; bağlantıya tıklayınca arama sizin tarayıcınızda açılır.</p>")
    satirlar = []
    for g in gruplar:
        adlar = [d.aday.ad for d in g.urunler]
        urunler = ", ".join(adlar[:3]) + (f" ve {len(adlar) - 3} ürün daha" if len(adlar) > 3 else "")
        satirlar.append([f"<b>{escape(g.tur)}</b>" + (f'<br><span class="soluk">{len(adlar)} ürün: {escape(urunler)}</span>' if len(adlar) > 1 else ""),
                         escape(g.cince_ad or "–"), escape(g.yurtdisi or "–"), f"<b>{escape(g.fiyat)}</b>" if g.fiyat else "bakılamadı",
                         escape(g.moq or "–"), escape(g.tedarikci or "–"),
                         " · ".join(_a("Fiyatın sayfası" if e.startswith("Tedarikçi sayfası") else e, adres) for e, adres in g.baglantilar) or "–"])
    p.append(_tablo(["Ürün türü", "Çince adı", "Yurt dışı fiyatı", "Çin'de fabrika fiyatı (liste)", "En az sipariş", "Tedarikçi", "Çin'de bakın"],
                    satirlar))
    return "".join(p)


def sayfa(sonuc: list[Degerlendirme], bugun: date, alan: str = "", acilmayan: str = "") -> str:
    yuk, cok, ady, dig = yukselenler(sonuc), cok_satanlar(sonuc), adaylar(sonuc), digerleri(sonuc)
    one_cikan = yuk + [d for d in cok if d not in yuk]
    siteler = {alan_adi(k) for d in sonuc for k in d.aday.kaynaklar if alan_adi(k)}
    tarihler = sorted(d.aday.veri_tarihi for d in sonuc if d.aday.veri_tarihi)
    baslik = (alan.strip() + ": " if alan.strip() else "") + "yurt dışında çok satanlar ve yükselenler"
    baslik = baslik[0].upper() + baslik[1:]
    fiyatli, cinceli = tedarik_sayilari(sonuc)

    p = ["<!doctype html>", '<html lang="tr"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         f"<title>{escape(baslik)}</title><style>{_STIL}</style></head><body><main>",
         '<div class="ust">Ürün araştırma raporu</div>', f"<h1>{escape(baslik)}</h1>",
         f'<div class="soluk">Rapor tarihi {tarih_yaz(bugun)} · {len(sonuc)} ürün · {len(siteler)} kaynak site'
         + (f" · en yeni satış verisi {tarih_yaz(tarihler[-1])}" if tarihler else "") + "</div>"]

    p.append('<div class="sayilar">'
             f'<div class="sayi"><b>{len(yuk)}</b>yükselen ürün</div>'
             f'<div class="sayi"><b>{len(cok)}</b>çok satan ürün</div>'
             f'<div class="sayi"><b>{len(ady)}</b>yazılarda geçen ürün</div>'
             f'<div class="sayi"><b>{fiyatli}</b>üründe Çin fabrika fiyatı</div></div>')
    ortak = iki_listede(sonuc)
    if ortak:
        p.append(f'<p class="soluk">{ortak} ürün hem yükselenler hem çok satanlar listesinde yer alıyor.</p>')
    if one_cikan:
        p.append("<p><b>Önce bakılacaklar</b></p><ul>" + "".join(
            f"<li><b>{escape(d.aday.ad)}</b> · {escape(d.sinif_gerekce)}</li>" for d in one_cikan[:3]) + "</ul>")
    else:
        p.append("<p>Görülen rakamlarla öne çıkan ürün bulunamadı. Aşağıda nedenleri yazıyor.</p>")
    p.append('<p class="soluk">Bu rapor, internette görülebilen sayfalardaki rakamlara dayanır; her rakamın kaynağı ve tarihi '
             "ürünün altında yazar. Ürünü görmek için altındaki “Ürünü gör” bağlantılarına tıklayın. Yurt dışında satması Türkiye'de satacağını "
             "göstermez.</p>")

    p.append('<h2>Yükselenler</h2><p class="soluk">Yeni parlayan ürünler: satışının büyük bölümü son 30 güne ait olanlar. '
             "Yükselişi yalnızca yazılara dayanan ürünler aşağıda, “Yazılarda geçenler” bölümündedir.</p>")
    p.append("".join(_kart(d) for d in yuk[:KART_SAYISI]) or "<p>Bu taramada yükselişi satış rakamıyla ölçülebilen ürün çıkmadı.</p>")
    if len(yuk) > KART_SAYISI:
        p.append(f"<p><b>Diğer yükselenler</b> ({len(yuk) - KART_SAYISI} ürün)</p>")
        p.append(_tablo(["Ürün", "Yükseliş", "Satış gücü", "Neden", "Kaynak"], [
            [_gorsel(d, "kucuk") + f"<b>{escape(d.aday.ad)}</b>" + _kimlik(d) + _uyari(d) + _incele(d, ("Ürünü gör", "Çin'de tedarik")),
             _puan(d.yukselis), _puan(d.satis), escape(" ".join(d.yukselis.aciklamalar)), _kaynaklar(d)] for d in yuk[KART_SAYISI:]], sag=(1, 2)))

    p.append('<h2>Çok satanlar</h2><p class="soluk">Satış sırası, satış adedi ve yorum sayısına göre en güçlü ürünler.</p>')
    if cok:
        p.append(_tablo(["Ürün", "Satış gücü", "Sıra", "30 günlük satış", "Toplam satış", "Yorum", "Yükseliş", "Kaynak"], [
            [_gorsel(d, "kucuk") + f"<b>{escape(d.aday.ad)}</b>" + ('<br><span class="soluk">yükselenlerde de var</span>' if d in yuk else "") + _kimlik(d)
             + _uyari(d) + _incele(d, ("Ürünü gör", "Çin'de tedarik")),
             _puan(d.satis), adet_yaz(d.aday.satis_sirasi) if d.aday.satis_sirasi else "–",
             adet_yaz(d.aday.son_satis * 30 / d.aday.son_satis_gun) if d.aday.son_satis is not None and d.aday.son_satis_gun else "–",
             adet_yaz(d.aday.toplam_satis) if d.aday.toplam_satis is not None else "–",
             adet_yaz(d.aday.yorum) if d.aday.yorum is not None else "–", _puan(d.yukselis), _kaynaklar(d)]
            for d in cok], sag=(1, 2, 3, 4, 5, 6)))
    else:
        p.append("<p>Bu taramada çok satan sayılabilecek ürün çıkmadı.</p>")

    p.append(_tedarik(sonuc, fiyatli, cinceli))

    if ady:
        p.append('<h2>Yazılarda geçenler</h2><p class="soluk">İzleme listesi: güncel yazılarda “viral” ya da “yükselen” diye anılan, '
                 "ama satış rakamı görülemeyen ürünler. Yükselişleri doğrulanmadı; Google Trends'te bakarak sınayabilirsiniz.</p>")
        satirlar = []
        for d in ady:
            n, son = guncel_ozet(d.aday, bugun)
            satirlar.append([_gorsel(d, "kucuk") + f"<b>{escape(d.aday.ad)}</b>" + _kimlik(d) + _uyari(d) + _incele(d, ("Ürünü gör", "Çin'de tedarik")), str(n) if n else "–", tarih_yaz(son) if son else "–",
                             escape(d.aday.trend or "–"), _kaynaklar(d)])
        p.append(_tablo(["Ürün", "Kaç sitede", "En yeni yazı", "Arama ilgisi", "Kaynak"], satirlar, sag=(1,)))

    if dig:
        p.append('<h2>Öne çıkmayanlar</h2><p class="soluk">Listeye girdi ama görülen rakamlar yeterli olmadı. '
                 "“Kanıt yetersiz” ürünün kötü olduğu anlamına gelmez; rakamı görülemedi demektir.</p>")
        p.append(_tablo(["Ürün", "Durum", "30 günlük satış", "Yorum", "Neden", "Kaynak"],
                        [[_gorsel(d, "kucuk") + f"<b>{escape(d.aday.ad)}</b>" + _kimlik(d) + _incele(d, ("Ürünü gör", "Çin'de tedarik")), escape(d.sinif),
                          adet_yaz(d.aday.son_satis * 30 / d.aday.son_satis_gun) if d.aday.son_satis is not None and d.aday.son_satis_gun else "–",
                          adet_yaz(d.aday.yorum) if d.aday.yorum is not None else "–",
                          escape(d.sinif_gerekce), _kaynaklar(d)] for d in dig], sag=(2, 3)))

    if derinlesti(sonuc):
        girilen = bilgi_girilenler(sonuc)
        p.append('<h2>Türkiye, kâr ve karar</h2><p class="soluk">Kâr = satış fiyatı − maliyet − komisyon − kargo. '
                 "KDV, gelir vergisi, iade ve reklam gideri dahil değildir. Yalnızca bilgi girdiğiniz ürünler gösterilir.</p>")
        p.append(_tablo(["Ürün", "Türkiye'de rekabet", "Ürün başına kâr", "Marj", "Karar", "Gerekçe"], [
            [f"<b>{escape(d.aday.ad)}</b>", escape(d.rekabet) + (f'<br><span class="soluk">{escape(tl(d.aday.tr_fiyat))}</span>' if d.aday.tr_fiyat else ""),
             escape(tl(d.kar.net)) if d.kar else "–", escape(yuzde_yaz(d.kar.marj)) if d.kar else "–",
             f"<b>{escape(d.karar)}</b>", escape(d.gerekce)] for d in girilen], sag=(2, 3)))

    p.append("<h2>Sıradaki adım: Türkiye kontrolü</h2>"
             "<p>Türkiye'deki pazaryerleri bu taramada okunamaz; bu kısmı sizin bakmanız gerekir. Ürün başına yaklaşık bir dakika sürer.</p><ol>"
             "<li>Aşağıdaki tabloda ürünün yanındaki bağlantıya tıklayın; pazaryerinde ürünün Türkçe adıyla arama açılır.</li>"
             "<li>İlk sayfada <b>gerçekten aynı ürün</b> olan ilanları sayın (sayfa bu ürünle doluysa 24 yazın, hiç yoksa 0).</li>"
             "<li>O ilanlardaki tipik satış fiyatını not edin.</li>"
             "<li>İsterseniz Google Trends'te ürün adını Türkiye ve “son 12 ay” seçerek aratın; eğri yükseliyor mu, düz mü, düşüyor mu?</li>"
             "<li>Bu rakamları ve ürünün size toplam maliyetini sohbete yazın ya da Excel dosyasındaki “Türkiye ve kâr” sayfasına girin.</li></ol>"
             f'<p class="soluk">{AZ_SATICI} ilana kadar “az satıcı”, {ORTA_SATICI} ilana kadar “orta”, üstü “kalabalık” sayılır.</p>')
    if one_cikan:
        p.append(_tablo(["Ürün", "Tek tıkla bakın", "Aynı ürün için ilan sayısı", "Tipik fiyat (TL)", "Toplam maliyet (TL)"],
                        [[escape(d.aday.ad), " · ".join(_a(e, adres) for e, adres in inceleme_baglantilari(d.aday)["Türkiye'de bak"]), "", "", ""]
                         for d in one_cikan[:15]]).replace("<td></td>", '<td class="bos"></td>'))

    p.append("<h2>Yöntem ve sınırlar</h2><ul>"
             "<li><b>Satış gücü (0–100):</b> satış sırası, 30 güne oranlanmış satış adedi, yorum sayısı ve toplam satış adedi. "
             f"{ESIK_SATIS} ve üstü “çok satan” sayılır.</li>"
             f"<li><b>Yükseliş (0–100):</b> satışın ne kadarının son 30 güne ait olduğu, satışın bir önceki aya göre artışı, son {YENI_GUN} "
             f"günde ürünü anlatan yazıların kaç ayrı sitede çıktığı ve arama ilgisinin yönü. {ESIK_YUKSELIS} ve üstü “yükselen” sayılır; "
             f"bunun için satış rakamı şarttır. {YENI_GUN} günden eski satış rakamı yükseliş sayılmaz.</li>"
             "<li>Pazaryeri satış adetleri çoğunlukla üçüncü taraf sitelerin <b>tahminidir</b> ve yuvarlak rakamlardır; kesin satış değildir.</li>"
             f"<li>Küçük rakamlar ölçülmez: toplam satışı {adet_yaz(IVME_TABAN)} adedin ya da aylık satışı {adet_yaz(ARTIS_TABAN)} adedin altındaki "
             "üründe yükseliş hesaplanmaz. Yorumuna göre çok satan ürün “yeni” sayılır ama tek başına yükselen sayılmaz.</li>"
             "<li>Görülemeyen işaret puanı düşürmez; “kanıt” düzeyini düşürür (kaç işaretin bilindiği).</li>"
             "<li>Satış rakamları tek bir haftanın ya da ayın görüntüsüdür ve bu verileri yayımlayan üçüncü taraf sitelerden alınmıştır; "
             "pazarın tamamını göstermez, zamanla değişir.</li>"
             "<li>Listelerdeki ürünlerin bir kısmı markalı ya da tek satıcıya özgü olabilir; aynısını getirmek mümkün olmayabilir.</li>"
             "<li><b>Çin tarafı:</b> 1688, Taobao, JD ve Pinduoduo gibi Çin siteleri otomatik okunamaz; rapor bunlar için ürüne özel arama "
             "bağlantısı verir, siz tıklayıp bakarsınız. “Çin'de fabrika fiyatı” yazıyorsa bu, üretici dizinindeki benzer ürünlerin liste "
             "fiyatıdır (çoğunlukla FOB, dolar); nakliye, gümrük ve vergi dahil değildir, pazarlıkla değişir ve maliyet hesabında kullanılmaz.</li>"
             "<li>Risk uyarıları ürün adı ve kategorisindeki kelimelere göre üretilen genel bilgidir. Uyarı çıkmaması ürünün serbest "
             "olduğunu göstermez; ithalat ve belge koşullarını gümrük müşavirinize sorun.</li>"
             "<li>Bu rapor bir satış garantisi ya da yatırım tavsiyesi değildir.</li>"
             + (f"<li>Bu taramada açılamayan kaynaklar: {escape(acilmayan.strip())}.</li>" if acilmayan.strip() else "") + "</ul>")
    p.append("<footer>Ürün Araştırma Agent'ı · Harun Gökce · github.com/Harungokc/eticaret-agentlari</footer></main></body></html>")
    return "\n".join(p)
