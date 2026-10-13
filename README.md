# E-ticaret Satıcısı için Yapay Zekâ Araçları Rehberi

**Trendyol, Hepsiburada, n11 ve Amazon'da satış yapanlar için: hangi iş için hangi açık kaynak yapay zekâ aracı
işe yarar, hangisi yaramaz, Türkiye'de ne eksik.**

GitHub'da e-ticaretle ilgili binlerce depo var; çoğu ya Amazon'a göre yazılmış, ya kurması teknik, ya da "açık
kaynak" etiketi yanıltıcı. Bu rehber 14 başlıkta 80'e yakın depoyu inceledi ve bir satıcının gerçekten
kullanabileceklerini ayıkladı. Türkiye pazaryerleri için eksik kalan yerlerde kendi araçlarımız var.

[![Testler](https://github.com/Harungokc/eticaret-agentlari/actions/workflows/test.yml/badge.svg)](https://github.com/Harungokc/eticaret-agentlari/actions/workflows/test.yml)
[![Lisans: MIT](https://img.shields.io/badge/lisans-MIT-blue.svg)](LICENSE)

> **Nasıl okunur.** Her araçta iki etiket var. **Kurulum:** *Kolay* (kod bilmeden, birkaç tıkla), *Orta* (adımları
> izleyerek yapılır), *Zor* (teknik bilgi ya da sunucu ister). **Durum:** *Denedik* (çalıştırıp sonucunu gördük),
> *Paketi doğruladık* (indirip yapısını denetledik), *İnceledik* (belgelerini ve kodunu okuduk, kurmadık).
> Yıldız sayıları 11 Ekim 2026 tarihlidir.

## Hızlı bakış

| İşiniz | Önerilen araç | Yıldız | Kurulum | Türkiye pazaryerine uygun mu |
|---|---|---|---|---|
| Hangi pazaryerinde elime ne kalır? | [Bu deponun araçları](#türkiye-pazaryerleri-için-bu-deponun-araçları) | — | Kolay | Evet |
| Fiyatım pazarda nerede, rakiplerime göre neredeyim? | [Bu deponun araçları](#türkiye-pazaryerleri-için-bu-deponun-araçları) | — | Kolay | Evet |
| Müşteriler neden şikâyet ediyor? | [Bu deponun araçları](#türkiye-pazaryerleri-için-bu-deponun-araçları) | — | Kolay | Evet |
| Satışlarım hangi illere gidiyor? | [Bu deponun araçları](#türkiye-pazaryerleri-için-bu-deponun-araçları) | — | Kolay | Evet |
| İlan ve satış metni yazmak | [marketingskills](https://github.com/coreyhaines31/marketingskills) | 54 bin | Kolay | Kısmen |
| Ürün fotoğrafını netleştirmek | [Upscayl](https://github.com/upscayl/upscayl) | 50 bin | Kolay | Evet |
| Arka plan silmek | [rembg](https://github.com/danielgatis/rembg) | 25 bin | Zor | Evet |
| Google ve Meta reklamlarını denetlemek | [claude-ads](https://github.com/AgriciDaniel/claude-ads) | 10 bin | Orta | Kısmen |
| Excel, PDF, sunum işleri | [anthropics/skills](https://github.com/anthropics/skills) | 180 bin | Kolay | Evet |
| Ürün ve pazar araştırması | [ecommerce-ai-skills](https://github.com/kangise/ecommerce-ai-skills) | 83 | Kolay (okumak) | Kısmen |
| İşleri birbirine bağlamak | [Activepieces](https://github.com/activepieces/activepieces) | 25 bin | Orta | Kısmen |
| Stok ve sipariş | [Dolibarr](https://github.com/Dolibarr/dolibarr), [ERPNext](https://github.com/frappe/erpnext) | 8 bin, 40 bin | Orta, Zor | Kısmen |
| Müşteri mesajlarını tek yerde toplamak | [FreeScout](https://github.com/freescout-help-desk/freescout), [Chatwoot](https://github.com/chatwoot/chatwoot) | 5 bin, 38 bin | Orta, Zor | Hayır |
| Satış panosu | [Metabase](https://github.com/metabase/metabase) | 50 bin | Zor | Kısmen |
| Kendi sitenizi asistana bağlamak | [mcp-adapter](https://github.com/WordPress/mcp-adapter), [shopify-mcp](https://github.com/GeLi2001/shopify-mcp) | 1,8 bin, 238 | Orta | Kendi sitesi olana |

---

## Türkiye pazaryerleri için: bu deponun araçları

Türkiye pazaryerleri için hazırlanmış, kurulum gerektirmeyen beş analiz aracı. **Durum: Denedik** (otomatik
testler Windows, macOS ve Linux'ta geçiyor; paketin Claude ve ChatGPT sohbet ekranına yüklenmesi her planda
denenmedi).

| Sorunuz | Araç | Sizden gereken |
|---|---|---|
| Hangi pazaryerinde elime ne kalır? | [Pazar ve Komisyon Analizcisi](01-pazar-ve-komisyon-analizcisi/) | Kategori ve satış fiyatı |
| Fiyatım nerede duruyor? Rakiplerime göre nerede gerideyim? | [Ürün, Fiyat ve Rakip Analizcisi](02-urun-fiyat-ve-rakip-analizcisi/) | Ürün listesi |
| Müşteriler neden şikâyet ediyor, üründe ne istiyor? | [Yorum Analizcisi](03-yorum-analizcisi/) | Ürün yorumları |
| Satışlarım hangi il, ilçe ve mahalleye gidiyor? | [Satış Bölge Analizcisi](04-satis-bolge-analizcisi/) | Sipariş listesi (il, ilçe, mahalle, tutar) |
| Yurt dışında ne çok satıyor, ne yeni yükseliyor, Çin'den kaça gelir? | [Ürün Araştırma Agent'ı](05-urun-arastirma-agenti/) | İlgilendiğiniz alan; kâr için Türkiye'deki ilan sayısı, maliyet ve satış fiyatı |

**Kurulum: tek dosya, üç adım**

1. **Paketi indirin:** [eticaret-analiz-araclari.zip](https://github.com/Harungokc/eticaret-agentlari/releases/latest/download/eticaret-analiz-araclari.zip) (ZIP'ten çıkarmayın).
2. **Asistanınıza yükleyin.**
   - **Claude:** *Customize → Skills → + → Upload a skill* deyip ZIP dosyasını seçin. *Settings → Capabilities*
     altında kod yürütme açık olmalıdır.
   - **ChatGPT:** Yeni sohbette ZIP dosyasını ekleyin ve şunu yazın: *"Bu ZIP dosyasını aç, içindeki SKILL.md
     dosyasını oku ve oradaki talimatlara göre çalış."*
3. **Sorun:** *"899 liralık kadın ayakkabıyı hangi pazaryerinde satmalıyım? Maliyetim 400 lira."*

Araçlar hesaplar, asistan anlatır: her rakam bu depodaki koddan gelir. Araçlar hiçbir pazaryerine bağlanmaz;
ürün listesini, yorumları ve siparişleri siz verirsiniz. Ayrıntılar, sınırlar ve gizlilik notları:
**[ARACLAR.md](ARACLAR.md)**

---

## Başlık başlık

### İlan ve satış metni

**[coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)** — 54 bin yıldız · MIT · Kurulum: Kolay ·
Durum: Paketi doğruladık

Claude için 50 pazarlama becerisi: metin yazımı, reklam metni, fiyatlandırma, müşteri araştırması, görsel,
sosyal medya ve daha fazlası. Her beceri için Claude'a doğrudan yüklenebilen hazır ZIP dosyası var.

- **Kurulum:** [Sürümler sayfasından](https://github.com/coreyhaines31/marketingskills/releases/latest)
  `copywriting-claude-web.zip` dosyasını indirin; Claude'da *Customize → Skills → Upload a skill* ile yükleyin.
  Satıcı için en ilgili beceriler: `copywriting`, `ad-creative`, `pricing`, `customer-research`, `image`, `social`.
- **Sınırı:** Yazılım şirketlerinin pazarlamasına göre yazılmış; İngilizce. Pazaryeri ilan kurallarını (başlık
  uzunluğu, yasaklı ifadeler) bilmez. Türkçe ilan metni için kullanılabilir, ama kuralları siz söylemelisiniz.

Fikir veren iki küçük depo: [amazon-listing-doctor](https://github.com/buluslan/amazon-listing-doctor) (82 yıldız, MIT; Amazon
ilanını puanlayan denetçi) ve Amazon'un resmi [selling-partner-agentic-toolkit](https://github.com/amzn/selling-partner-agentic-toolkit)
deposu. İkisi de Amazon'a göre; Türkiye pazaryerlerinin kurallarını bilen bir ilan denetçisi yok.

### Ürün görseli

**[Upscayl](https://github.com/upscayl/upscayl)** — 50 bin yıldız · AGPL · Kurulum: Kolay · Durum: İnceledik

Bulanık ya da küçük ürün fotoğrafını büyütüp netleştiren masaüstü uygulaması. Windows, macOS ve Linux için
kurulum dosyası var; fotoğraflar bilgisayarınızdan çıkmaz. Son kararlı sürümü Aralık 2024 tarihli.

**[rembg](https://github.com/danielgatis/rembg)** — 25 bin yıldız · MIT · Kurulum: Zor · Durum: İnceledik

Fotoğrafın arka planını siler. Komut satırından çalışır; kod bilmeyen biri için uygun değil, ama toplu işlem
için güçlü.

Pazaryerlerinin görsel kurallarını (beyaz zemin, ölçü, ret nedenleri) denetleyen bir araç bulamadık.

### Reklam

**[claude-ads](https://github.com/AgriciDaniel/claude-ads)** — 10 bin yıldız · MIT · Kurulum: Orta · Durum: İnceledik

Google, Meta ve diğer reklam hesaplarını denetleyen Claude eklentisi. Varsayılan olarak yalnızca okur;
değişiklik yapması ayrıca açılmadıkça kapalıdır. Claude Code ile kurulur; ajanslara ve danışmanlara göre
tasarlanmış.

**[google-ads-mcp](https://github.com/googleads/google-ads-mcp)** — 1 bin yıldız · Apache-2.0 · Kurulum: Zor · Durum: İnceledik

Google Ads hesabını asistana bağlar; yalnızca sorgu yapar. Depo `googleads` kuruluşuna ait.

**Sınır:** İkisi de Google ve Meta reklamları için. Trendyol ve Hepsiburada'nın kendi reklam panelleri için
açık kaynak bir araç bulamadık.

### Ürün ve pazar araştırması

**[kangise/ecommerce-ai-skills](https://github.com/kangise/ecommerce-ai-skills)** — 83 yıldız · CC0 · Kurulum: Kolay (okumak) ·
Durum: İnceledik

Tedarikten büyümeye 69 bölümlük bir e-ticaret bilgi tabanı ve hazır istemler; İngilizce, Çince ve Japonca.
[Çevrimiçi okunabilir](https://kangise.github.io/ecommerce-ai-skills/en/); ücretli veri servisi istemez.
Sınır ötesi satışa ve Amazon'a göre yazılmış.

**Sınır:** Bu alandaki popüler depoların çoğu (ör. 950 yıldızlı bir Amazon ürün araştırma deposu) ücretli veri
servislerine bağlıdır ve Türkiye pazaryerlerini kapsamaz. Türkiye için bir veri katmanı yok; araştırmayı
kendi topladığınız listeyle yapmanız gerekir ([Ürün, Fiyat ve Rakip Analizcisi](02-urun-fiyat-ve-rakip-analizcisi/)).

### Yorum analizi

Türkçe yorumlar için bu deponun [Yorum Analizcisi](03-yorum-analizcisi/). Alternatif:
**[review-analyzer-skill](https://github.com/buluslan/review-analyzer-skill)** (132 yıldız · MIT · Kurulum: Orta · Durum:
İnceledik): yorumlardan 15 bölümlük rapor ve pano üretir; Claude Code gibi bir kodlama asistanı ister, belgeleri
Çince ağırlıklıdır ve Türkçe yorumla denenmemiştir.

### Dosya işleri: Excel, PDF, sunum

**[anthropics/skills](https://github.com/anthropics/skills)** — 180 bin yıldız · Kurulum: Kolay · Durum: İnceledik

Claude'un Excel, Word, PowerPoint ve PDF becerileri; Claude'da hazır gelir, ayrıca kurmanız gerekmez. Depodaki
belge becerilerinin hakları saklıdır (açık kaynak değildir), ama kullanımı ücretsizdir.

**[markitdown](https://github.com/microsoft/markitdown)** — 189 bin yıldız · MIT · Kurulum: Orta · Durum: İnceledik

PDF, Word ve Excel dosyalarını yapay zekânın okuyabileceği düz metne çevirir.

### Otomasyon

**[Activepieces](https://github.com/activepieces/activepieces)** — 25 bin yıldız · çekirdeği MIT · Kurulum: Orta · Durum: İnceledik

"Sipariş gelince şunu yap" türü iş akışları kurmaya yarar. Hazır bir Trendyol ya da Hepsiburada bağlayıcısı
olduğunu doğrulayamadık.

### Stok ve sipariş

**[Dolibarr](https://github.com/Dolibarr/dolibarr)** (8 bin yıldız · GPL · Kurulum: Orta) ve **[ERPNext](https://github.com/frappe/erpnext)**
(40 bin yıldız · GPL · Kurulum: Zor) — Durum: İnceledik

Stok, sipariş, fatura ve muhasebe yazılımları. Dolibarr Windows'a kurulabilir; ERPNext sunucu ister. İkisinin de
Türkiye pazaryerleriyle hazır bağlantısı yok.

### Müşteri mesajları

**[FreeScout](https://github.com/freescout-help-desk/freescout)** (5 bin yıldız · AGPL · Kurulum: Orta) ve
**[Chatwoot](https://github.com/chatwoot/chatwoot)** (38 bin yıldız · Kurulum: Zor) — Durum: İnceledik

E-posta ve sohbet mesajlarını tek kutuda toplar. Kendi sitesi olan satıcıya uyar; pazaryeri sorularını
bağlamazlar. Chatwoot'un yapay zekâ ajanı ("Captain") deponun ücretli lisanslı bölümündedir.

### Satış panosu

**[Metabase](https://github.com/metabase/metabase)** — 50 bin yıldız · açık çekirdek · Kurulum: Zor · Durum: İnceledik

Satış verisinden grafik ve pano üretir. Veritabanı ve sunucu ister; bazı özellikleri ücretlidir.

### Kendi siteniz

**[WordPress/mcp-adapter](https://github.com/WordPress/mcp-adapter)** (1,8 bin yıldız · GPL) ve
**[shopify-mcp](https://github.com/GeLi2001/shopify-mcp)** (238 yıldız · MIT) — Kurulum: Orta · Durum: İnceledik

WooCommerce ya da Shopify mağazanızı yapay zekâ asistanına bağlar: ürün, sipariş ve müşteri bilgisine
sohbetten erişirsiniz. ikas, Ticimax ve IdeaSoft için mağaza sahibine yönelik benzer bir açık kaynak bağlantı
bulamadık.

---

## Popüler ama listede olmayanlar

Aramalarda öne çıkan bazı depolar rehbere alınmadı. Nedenleri depoların kendi dosyalarından doğrulanabilir.

| Depo | Yıldız | Neden listede değil |
|---|---|---|
| [n8n](https://github.com/n8n-io/n8n) | 207 bin | Güçlü bir otomasyon aracı, ama lisansı ("Sustainable Use License") açık kaynak değil: kendi işiniz için kullanabilirsiniz, ticari olarak dağıtmak kısıtlıdır. |
| [google-ads-meta-ads-mcp](https://github.com/irinabuht12-oss/google-ads-meta-ads-mcp) | 4,4 bin | Depoda kaynak kod dosyası yok; yalnızca belge ve ayar dosyaları var. Barındırılan bir servise bağlanır. |
| [meta-ads-mcp](https://github.com/pipeboard-co/meta-ads-mcp) | 1,3 bin | Lisansı Business Source License; açık kaynak değil. |
| [nexscope-ecommerce-skills](https://github.com/nexscope-ai/nexscope-ecommerce-skills) | 85 | README'sine göre lisansı kapalı ("proprietary"); API anahtarı ve kredi ister. |
| [IOPaint](https://github.com/Sanster/IOPaint) | 23 bin | Arşivlenmiş; Nisan 2025'ten beri güncellenmiyor. |
| [changedetection.io](https://github.com/dgtlmoon/changedetection.io) | 35 bin | İyi bir sayfa takip aracı, ama pazaryeri sayfalarını otomatik izlemek kullanım koşullarına aykırı olabilir ve hesabınızı riske atabilir. Tedarikçi sitesi gibi izin verilen sayfalar için kullanın. |
| E-posta pazarlama araçları ([listmonk](https://github.com/knadh/listmonk) vb.) | 24 bin | Pazaryeri, müşterinin e-postasını satıcıya vermez; izinsiz gönderimin yasal riski vardır. Yalnızca kendi sitesi ve onaylı listesi olan satıcıya uyar. |

**Yıldız sayısı tek başına ölçü değil.** Bir depoyu kullanmadan önce üç şeye bakın: lisans dosyası var mı, son
güncelleme ne zaman, depoda gerçekten kod var mı.

---

## Türkiye'de eksik olanlar

İncelemede, Türkiye'deki pazaryeri satıcısı için açık kaynak karşılığı bulunmayan işler:

1. **Pazaryeri dökümlerinden gerçek kâr.** Hakediş, komisyon, kargo, iade ve reklam dosyalarından ürün bazında
   net kârı çıkaran araç. Dört ayrı inceleme kolunda da eksik çıktı.
2. **Türkiye pazaryeri kurallarını bilen ilan denetçisi.**
3. **Müşteri sorusuna cevap taslağı:** ürün bilgisine dayanan, göndermeyi satıcının onayına bırakan hafif araç.
4. **Çok pazaryerli stok özeti:** "şu ürün bitiyor", "kanallar arasında tutarsızlık var".
5. **Pazaryeri reklam raporu analizi.**
6. **Trendyol dışındaki pazaryerleri.** Trendyol için birkaç yeni bağlantı deposu var (hepsi 10 yıldızın
   altında); Hepsiburada, n11, Çiçeksepeti, Pazarama ve Amazon Türkiye için bir şey bulamadık.

Sıradaki araç birincisi olacak. **Bunun için gerçek döküm örneklerine ihtiyacımız var:** bir pazaryerinden
indirdiğiniz hakediş ya da sipariş dökümünü (müşteri bilgilerini silerek) paylaşabilirseniz, araç sizin
dosyanızla çalışacak şekilde yazılır. İletişim aşağıda.

---

## Yöntem ve sınırlar

- **Kapsam:** 14 başlıkta 80'e yakın depo, 9–11 Ekim 2026. Her depo için GitHub verisinden yıldız, kopya, açık
  sorun, tarih ve lisans alındı; README ve dosya yapısı okundu.
- **Denemeler:** Yalnızca bu deponun araçları çalıştırılarak denendi. Diğer depolar kurulmadı; "Durum" etiketi
  her birinde ne yapıldığını söyler.
- **Eksikler:** GitHub araması her depoyu göstermez; listede olmayan iyi araçlar olabilir. Çiçeksepeti, Pazarama,
  Sentos, Dopigo ve IdeaSoft için ayrı arama yapılamadı.
- **"Eksik" listesi** depo taramasından çıkmıştır; satıcıların bunları gerçekten isteyip istemediğini göstermez.
- Bu rehber Trendyol, Hepsiburada, n11, Amazon ya da adı geçen depoların sahipleriyle bağlantılı değildir.

Bir depo hakkında yanlış ya da eski bir bilgi görürseniz
[bildirin](https://github.com/Harungokc/eticaret-agentlari/issues); düzeltiriz.

## Lisans

Bu deponun kodu ve rehber metni [MIT](LICENSE) lisanslıdır. Bağlantı verilen depoların her biri kendi lisansına
tabidir.

## Geliştiren

**Harun Gökce** — harungokce70@gmail.com · 0506 155 46 42

Bu araçlardan birini işletmenize kurmak, kendi verinizle bir analiz yaptırmak ya da "eksik olanlar"dan birini
birlikte geliştirmek isterseniz yazabilirsiniz.
