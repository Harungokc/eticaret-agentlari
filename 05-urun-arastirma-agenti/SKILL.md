---
name: urun-arastirma-agenti
description: Türkiye'deki e-ticaret satıcıları için, satıcının alanında (ör. mutfak, evcil hayvan, hamilelik, kişisel bakım) yurt dışında şu an çok satan ve yeni yükselen (viral) ürünleri internette derinlemesine tarar; her ürünü adı, fiyatı, fotoğrafı, bağlantısı ve satış rakamlarıyla listeleyen kaynaklı bir rapor hazırlar. Kullanıcı "yurt dışında hangi ürünler tutuyor", "viral ürün bul", "ne satsam", "çok satan ürünler neler", "yeni ürün fikri", "bu ürünü getirsem kâr eder miyim" gibi sorular sorduğunda ya da ürün listesi verdiğinde kullan. Sonucu rapor sayfası (HTML) ve Excel dosyası olarak verir. Araştırma (Research) modunda değil, normal sohbette çalışır.
---

# Ürün Araştırma Agent'ı

İş iki parçadır. **Taramayı sen yaparsın:** internette arama yapıp kullanıcının alanında yurt dışında çok
satan ve yükselen ürünleri, gördüğün rakamlar, bağlantılar ve tarihleriyle toplarsın. **Hesabı ve raporu
bu klasördeki Python aracı yapar:** ürünleri iki puanla (satış gücü, yükseliş) sınıflar, rapor sayfasını
ve Excel dosyasını üretir. Araç internete bağlanmaz, ek paket gerektirmez (Python 3.10+).

Bu klasör sana bir ZIP dosyası olarak verildiyse (ör. ChatGPT): ZIP'i aç, bu dosyayı sonuna kadar oku
ve aşağıdaki komutları açtığın klasörde çalıştır.

## Hedef: satıcının işine yarayan bir rapor

Satıcı bu raporu açtığında **ürünleri görmek** ister: hangi ürün, kim satıyor, kaça, ayda kaç adet,
artıyor mu. Üç-beş ürünlük bir rapor işe yaramaz. İyi bir tarama:

- **40-80 ürün** toplar; her birinin gerçek adı, fiyatı, bağlantısı ve en az bir satış rakamı vardır.
- Alanı tek bir aramayla değil, **8-12 alt ürün türüne bölerek** tarar.
- **Her alt ürün türü için Çin tarafını da getirir:** Çince arama adı ve Çin'deki fabrika liste fiyatı
  (2. adım, F). Satıcı ürünü Çin'den alır; yalnızca yurt dışı satış rakamı veren rapor yarımdır.
- En az 15-20 dakika sürer ve 60-90 sayfa açar. Bu normaldir; kısa kesme.

Rakam yoksa uydurma, ama rakam bulunabilecekken erken de bırakma.

## Kurallar

1. **Rakam uydurma.** Listeye yazdığın her rakam, ad, bağlantı ve tarih bu konuşmada açıp gördüğün bir
   sayfadan gelmeli ve o sayfa `kaynak` sütununda durmalı. Hatırladığın ya da tahmin ettiğin değeri
   yazma; hücreyi boş bırak. Boş hücre sorun değildir: araç onu "görülemedi" sayar.
2. **Sayfayı gerçekten gördüysen yaz.** Bazı sayfalar hata vermeden boş gelir (yalnızca başlık, menü ya
   da "veri yok"). Ürün satırlarını görmediysen o sayfayı kaynak sayma.
3. **Arama özetine güvenme.** Arama sonucunun özet satırındaki rakamın tarihi belli değildir. Sayfayı
   açamadıysan o rakamı yazma.
4. **Engeli aşmaya çalışma.** Sayfa açılmıyorsa (403, 503, giriş ekranı, robot doğrulaması, "tümünü
   görmek için üye ol") bırak ve sıradakine geç. Açılmayan siteleri not et; raporda yazacak. Aynı sitenin
   herkese açık başka bir kategori, ülke ya da anahtar kelime sayfasını açmak engel aşmak değildir.
5. **Dolgu yapma, kapsamı genişlet.** Ürün sayısı azsa çözüm rakamsız ürün eklemek değil, daha çok alt
   ürün türüne bakmaktır.
6. **Puanı, sınıfı, kârı ve kararı kendin hesaplama.** Hepsi aracın çıktısından gelsin. Aracı
   çalıştıramıyorsan rakam verme; çalıştıramadığını söyle.
7. **Maliyeti kullanıcı verir.** Ürünün kapıya kadarki toplam maliyetini (alış, taşıma, gümrük, vergi;
   TL) tahmin etme, gümrük vergisi hesaplama.
8. **Satış vaadi verme.** Yurt dışında satması Türkiye'de satacağını göstermez. "Kesin satar",
   "garantili" gibi ifadeler kullanma. Aracın uyarı ve `Not:` satırlarını kullanıcıya aktar.
9. **Çin'de tedarik her taramada yapılır.** Alan ne olursa olsun (mutfak, hamilelik, evcil hayvan, oto
   aksesuar…) her alt ürün türü için F adımını uygula; süre azalırsa ürün sayısını azalt, F'yi atlama.
   Okunamayan Çin sitelerini zorlamak ya da fiyat tahmin etmek bunun yolu değildir (kural 1 ve 4).
10. İnternette arama yapamıyorsan bunu açıkça söyle; kullanıcı aramayı açsın. Arama yapamadan ürün
   listesi üretme.

## 1. Adım: Alanı öğren ve tarama planını kur

Tek soru yeter: **hangi alan ya da ürün türü?** Kullanıcı yazdıysa sorma. Maliyet, komisyon ve Türkiye
bilgisi ilk rapor için gerekmez.

Sonra alanı **8-12 alt ürün türüne** böl ve her biri için bir İngilizce alışveriş ifadesi
(müşterinin arama kutusuna yazacağı gibi, küçük harf) ve **Çince arama adını** yaz (ör. `pregnancy
pillow` / `孕妇枕`). Örnek, "hamilelik ürünleri" için:

`pregnancy pillow` · `maternity belly band` · `nursing bra` · `maternity leggings` · `postpartum
underwear` · `stretch mark cream` · `nursing pillow` · `breast pump` · `hospital bag` · `maternity dress`

Alt türleri seçerken: satıcının getirebileceği fiziksel ürünleri öncele; yalnızca büyük markaların
sattığı ya da izne bağlı türleri (ilaç, takviye, mama) en fazla bir-iki tane al. Kullanıcıya planı tek
cümleyle ve taramanın birkaç dakika süreceğini söyle, sonra başla; onay bekleme.

## 2. Adım: Tara

Kaynaklar aşağıda. A ve B satışı, D ve E yükselişi, **F Çin'deki tedariki** verir; A, B ve F her
taramada yapılır. **Her alt türü A'da taradıktan hemen sonra o türün F sayfasını da aç**; F'yi sona
bırakırsan süre bitince eksik kalır. Site adları Ekim 2026'da açılabilen örneklerdir; biri açılmazsa aynı
işi gören bir başkasını aramayla bul (ör. `amazon keyword report top products units sold <ifade>`).

### A. Pazaryeri anahtar kelime raporları (taramanın omurgası)

Amazon'un kendi sayfaları açılmaz; anahtar kelime başına satış raporu yayımlayan siteler açılır.
**asinsight.com** her alışveriş ifadesi için iki sayfa verir. İfadeyi tireyle yaz ve **her alt ürün türü
için ikisini de aç**:

- `https://www.asinsight.com/report/US/<ifade>` (ör. `.../report/US/pregnancy-pillow`)
- `https://www.asinsight.com/market-analysis/US/<ifade>`

Her sayfada 10 ürün satırı ve çoğu zaman **"Fastest Growing"** ile **"New to Top 10"** blokları vardır;
bu bloklardaki ürünler ilk 10'un dışından da olabilir, onları da al.

- Sayfayı açarken okuma aracından **açıkça** iste: her ürünün tam başlığı, ASIN kodu, fotoğraf adresi,
  fiyatı, aylık satış adedi, yorum sayısı ve değişim yüzdesi; ayrıca sayfanın ait olduğu ay. İstemezsen
  araç bunların bir kısmını özetlerken atar.
- Adres 404 verirse ifadeyi değiştir (`maternity-leggings-for-women`, `pregnancy-pillows-for-sleeping`).
  Çalışan ifadeleri bulmanın en iyi yolu `/market-analysis` sayfasının altındaki "Related" bağlantılarıdır
  (`/report` sayfasının altındaki bağlantılar çoğu zaman ilgisizdir). Olmazsa `asinsight.com report US
  "<ifade>"` diye ara.
- İki sayfanın tarihi farklıysa **yeni olanı** esas al. `/report` sayfaları bazen aylarca eskidir ve
  ilgisiz ürünlerle doludur; öyleyse o sayfayı kullanma. Aynı aya ait iki sayfa aynı ürün için farklı
  satış adedi veriyorsa **düşük olanı** yaz ve farkı `not`a ekle.

Her ürün satırından şunları al:

| Sayfada | Sütun |
|---|---|
| Ürün başlığı (tam) | `orijinal_ad` |
| ASIN (B0 ile başlayan kod) | `urun_link` = `https://www.amazon.com/dp/<ASIN>` |
| Ürün fotoğrafının adresi (https ile başlıyorsa) | `gorsel` |
| Fiyat | `yurtdisi_fiyat` (ör. `$24.89`) |
| "Units Sold/mo" (aylık satış tahmini) | `son_satis`, ve `son_satis_gun` = `30` |
| Yorum sayısı (yıldızın yanındaki, ör. 25.1K) | `yorum` |
| "MoM" değişim yüzdesi (▲ / ▼) | `satis_degisim` (düşüşse eksi: `-12`); aşağıdaki nota bak |
| Sayfa başlığındaki ay (ör. July 2026) | `veri_tarihi` = `2026-07` |

Dikkat edilecekler:

- **Sayfadaki sıra numarasını `satis_sirasi`na yazma.** O, tek bir arama ifadesindeki sıradır;
  pazaryerinin kategori sırası değildir ve küçük bir ifadede 1. olmak çok satmak demek değildir.
- **Tarihi her sayfadan oku.** Raporların yaşı 1 ile 6 ay arasında değişir. Aracın kuralı: 120 günden
  eski satış rakamı yükseliş sayılmaz. Bir alt tür için rapor eskiyse yakın bir ifadeyi de dene.
- Satış adetleri **tahmindir** ve yuvarlaktır (10.000, 5.000). Olduğu gibi yaz.
- **Değişim yüzdesinde iki sayfa çelişebilir** (birinde +%67, diğerinde -%10). `satis_degisim`i
  `/market-analysis` sayfasındaki "MoM" değerinden al. İki sayfa ters yön gösteriyorsa `satis_degisim`i
  **boş bırak** ve `not`a ikisini de yaz; çelişkili rakamla ürünü yükselen gösterme.
- Araç aylık satışı 2.000 adedin altındaki üründe artış yüzdesini saymaz (200 adetten 400'e çıkmak %100
  görünür) ve artış rakamı olmayan ürünü yükselen saymaz. Yani asıl değerli olanlar **hem satan hem
  artan** ürünlerdir: "Fastest Growing" ve "New to Top 10" bloklarını ve değişim yüzdelerini kaçırma.
- Arama sonuçları karışıktır: ifadeyle ilgisi olmayan ürünü (ör. "hamile yastığı" aramasında vitamin ya
  da genel yastık) **alma**.
- Aynı ürün (aynı ASIN) birden çok ifadede çıkarsa **tek satır** yaz. Aynı ürünün yalnızca rengi ya da
  bedeni farklı olan ilanlarını da tek satırda topla; çok satanı al, diğerini `not`a yaz.
- Sayfanın üstündeki arama hacmi değişimi alt türün kendisinin yükselip yükselmediğini gösterir. Aylık
  arama hacmi **%20 ya da daha fazla** artmışsa o alt türün ürünlerinde `trend` = `yükseliyor` yaz ve
  rakamı `not`a ekle; azsa ya da haftalık ile aylık değişim çelişiyorsa boş bırak.

### B. Video alışveriş (TikTok Shop) haftalık listeleri

**findniche.com** kategori ve ülke başına haftalık liste verir:
`https://findniche.com/tiktok/trending-<kategori>-products-<ülke>`

- Kategoriler: `kitchenware`, `home-supplies`, `household-appliances`, `furniture`,
  `textiles-and-soft-furnishings`, `tools-and-hardware`, `baby-and-maternity`, `kids-fashion`,
  `toys-and-hobbies`, `pet-supplies`, `beauty-and-personal-care`, `health`, `sports-and-outdoor`,
  `phones-and-electronics`, `luggage-and-bags`, `food-and-beverages`.
- Ülkeler: `us` ve `gb` (ikisine de bak). Alanla ilgili **bütün** kategorilerin sayfalarını aç.
- Her sayfada 10 ürün: ad, fiyat, toplam satış, son 7 gün satış. Sayfadaki "Updated at" tarihini
  `veri_tarihi`na yaz.

| Sayfada | Sütun |
|---|---|
| Ürün adı | `orijinal_ad` |
| Fiyat | `yurtdisi_fiyat` |
| 7-day Sales | `son_satis`, ve `son_satis_gun` = `7` |
| Total Sales | `toplam_satis` |

- **Toplam satış 7 günlük satışa eşitse `toplam_satis`ı boş bırak**; bu, toplamın bilinmediğini gösterir.
- Bu listelerin yarısı alanla ilgisiz olabilir; yalnızca alana uyan ürünleri al. Araç toplam satışı
  10.000 adedin altındaki üründe yükselişi ölçmez.
- Gelir (GMV) sütunu tutarsızdır; kullanma. Listedeki sıra numarasını `satis_sirasi`na yazma.
- Bu sayfalarda ürün bağlantısı yoktur; `urun_link`i boş bırak (araç arama bağlantısı üretir).

### C. Ek satış kaynakları (zamanın kalırsa)

Bunlar isteğe bağlıdır; A ve B'yi tamamlamadan buraya zaman harcama.

- **Kategori çok satanlar sırası:** Amazon aylık sıralama raporu, ör.
  `https://metricscart.com/bestseller-reports/amazon-com/categories/Home%20&%20Kitchen/`. Yalnızca ilk 10
  ürün okunur. Buradaki sıra gerçek kategori sırasıdır: `satis_sirasi` ve `yorum`.
- **Büyük mağaza kategori sayfaları** (Target, IKEA, Best Buy, Otto): yorum sayısı; "geçen ay 4.000+
  satıldı" gibi bir rakam varsa `son_satis` = 4000, `son_satis_gun` = 30. "Yeni" ya da "çok satan"
  rozetini `not`a yaz.

### D. Güncel yazılar (viral diye anılan ürünler)

Arama örnekleri: `viral <alan> products 2026`, `tiktok made me buy it <alan>`. Aradığın, ürünü **"viral",
"yükselen" ya da "yeni çıkan" diye anlatan** yazılardır; genel "en çok satanlar" yazıları ve indirim
listeleri sayılmaz. Yalnızca **tarihini sayfada gördüğün** ve son 120 günde çıkmış yazıları al; hem yayın
hem güncelleme tarihi varsa yayın tarihini yaz. Üç farklı arama yap; marka basın bültenlerini bağımsız
yazı sayma. Bazı alanlarda güncel yazı bulunmaz; bulamadıysan bunu kullanıcıya söyle, eski yazı kullanma.

- Yazıdaki ürün A ya da B'de bulduğun bir ürünle **aynıysa** (aynı marka ve model; markasız üründe
  aynı ürün türü ve belirgin özelliği, ör. "titanyum kesme tahtası") yazının bağlantısını o ürünün
  `kaynak`ına, tarihini `kaynak_tarihi`na ekle. Markasız türde yazıyı en çok satan en fazla üç ürüne
  ekle. Bu, ürünün yükseliş puanını artırır.
- Değilse ve alan için önemliyse ayrı satır yaz; satış rakamı olmadığı için raporda "yazılarda
  geçenler" izleme listesine düşer. Sonra o ürün türü için A'daki raporu açmayı dene: çoğu zaman satış
  rakamı oradan gelir.

### E. Arama ilgisi

Bir ürün türünün arama ilgisinin **son aylarda** arttığını gösteren sayfa gördüysen (asinsight
sayfasının üstündeki arama hacmi değişimi, meetglimpse.com/trends, treendly.com, explodingtopics.com) o
türdeki ürünlerin `trend` sütununa `yükseliyor` yaz. Birkaç yıllık büyüme gösteren sayfa için `trend`i
boş bırak, `not`a yaz. Yalnızca böyle bir listede gördüğün, başka kaynağı olmayan ürünü ekleme.

### F. Çin'de tedarik (her taramada, her alt ürün türü için)

Satıcı için asıl soru ürünü Çin'den kaça alacağıdır. Çin'in büyük siteleri (1688, Taobao, Tmall, JD,
Pinduoduo, Douyin, Alibaba, AliExpress, Temu) sana **açılmaz**; boş sayfa ya da robot doğrulaması gelir.
Bunları zorlamadan geç: araç her ürün için bu sitelerde arama bağlantısı üretir, satıcı tıklayıp bakar.
Senin yapacağın iki şey var:

1. **Çince arama terimi.** Listedeki **her ürün** için `cince_ad` sütununa ürün türünün Çince adını yaz
   (ör. hamile yastığı → `孕妇枕`, titanyum kesme tahtası → `钛砧板`, yağ püskürtme şişesi → `喷油瓶`).
   Aynı türdeki ürünlere aynı terimi yaz; belirgin özelliği olan üründe özelliği de ekle (cam, titanyum,
   elektrikli). Bu bir çeviridir, rakam değildir; emin olmadığın terimi yazma. Araç 1688 ve Taobao
   aramasını bununla kurar; terim yoksa o ürün için bu iki bağlantı çıkmaz.
2. **Fabrika fiyatı.** Üretici dizini **made-in-china.com** açılır. Her alt ürün türü için bir sayfa aç:
   `https://www.made-in-china.com/multi-search/<İngilizce+ifade, boşluk yerine %2B>/F1/1.html`
   (ör. `.../multi-search/U%2BShaped%2BPregnancy%2BPillow/F1/1.html`). Sayfada ürün başına fiyat aralığı
   (dolar, FOB), en az sipariş adedi (MOQ), üretici adı ve ili yazar.

   - Yalnızca **başlığı gerçekten aynı ürün olan** satırları al. Sayfaların yarısı ilgisiz ürünle
     dolabilir (ör. "nursing pads" aramasında hasta bezi); başlığa bakmadan fiyat alma.
   - En az **üç ayrı tedarikçi** gerekir (aynı şirketin iki adı tek sayılır). Bulamazsan ifadeyi bir kez
     değiştir (ör. `Postpartum%2BBelt`, `Disposable%2BBreast%2BPad`); yine olmazsa o tür için tedarik
     sütunlarını **boş bırak**.
   - Şu satırları sayma: tek satırda en yüksek fiyatı en düşüğünün 4 katını aşanlar (`$1.25-6.90`),
     diğerlerinden çok kopuk tek fiyatlar, `$1.00` gibi göstermelik fiyatlar, adet yerine kutu, paket,
     çift ya da metre fiyatı verenler, ürünün yalnızca parçası ya da ambalajı olanlar.
   - `tedarik_fiyat`: kalan satırların en düşük ve en yüksek fiyatı, para birimiyle (ör. `$4.25-10.00`).
   - `tedarik_moq`: en az sipariş aralığı (ör. `20-500`).
   - `tedarikci`: kaç tedarikçiye baktığın ve illeri (ör. `5 tedarikçi; Guangdong, Zhejiang`). Çoğu
     üretici değil, ticaret şirketidir; "üretici" deme.
   - `tedarik_link`: fiyatı aldığın sayfanın bağlantısı.
   - Aynı alt türdeki ürünlere aynı tedarik bilgisini yaz; ürün belirgin biçimde farklıysa (ör. titanyum
     yerine bambu, doğum sonrası kuşak yerine hamile kuşağı) ayrı ara ya da boş bırak.
   - Tek kullanımlık ürünlerde fiyat tane başınadır ve en az sipariş on binlerle ölçülür; bunu `not`a yaz.

Bu fiyat **liste fiyatıdır**: nakliye, gümrük, vergi ve pazarlık dahil değildir. Bundan maliyet ya da kâr
hesaplama; `maliyet` sütununa yazma. Kullanıcıya "Çin'de üretici liste fiyatı" diye sun.

Çin'de neyin çok sattığını gösteren, okunabilir bir kaynak yoktur; "Çin'de çok satıyor" deme. Kullanıcı
1688 ya da Taobao'da gördüğü satış adedini sana yazarsa `not`a ekle.

## 3. Adım: Yeterince taradın mı?

Listeyi yazmadan önce kendine sor:

- En az **8 alt ürün türü** için A'daki iki sayfayı açtım mı?
- B'de alanla ilgili her kategorinin `us` ve `gb` sayfasına baktım mı?
- Satış rakamı olan en az **30 ürünüm** var mı? Yoksa plana yeni alt türler ekleyip A'ya dön.
- Her üründe `orijinal_ad` dolu mu? Amazon ürünlerinde `urun_link` dolu mu?
- Her satış rakamının `veri_tarihi` var mı?
- D'de güncel yazı aradım mı (üç arama)?
- **Her üründe** `cince_ad` dolu mu? **Her alt tür için** F'deki fabrika fiyatı sayfasını açtım mı?
  (Bakıp bulamadığın tür boş kalır; hiç bakmadığın tür kalmamalı.)
- Alanla ilgisi olmayan ürünleri ayıkladım mı?

Araç ya da süre sınırına takılıp bunları tamamlayamadıysan topladığınla devam et ve kullanıcıya **kaç
alt türe bakabildiğini, neyin eksik kaldığını** açıkça söyle.

## 4. Adım: Listeyi yaz

Noktalı virgülle ayrılmış bir CSV dosyası yaz (elle değil, kısa bir Python betiğiyle ve `csv` modülüyle
yaz ki tırnak ve ayırıcı hatası olmasın). İlk satır aynen şu olsun:

```
ad;kategori;marka;orijinal_ad;cince_ad;urun_link;gorsel;yurtdisi_fiyat;tedarik_fiyat;tedarik_moq;tedarikci;tedarik_link;ulke;kaynak;kaynak_tarihi;satis_sirasi;yorum;son_satis;son_satis_gun;toplam_satis;satis_degisim;veri_tarihi;izlenme;trend;tr_satici;tr_fiyat;tr_kontrol;tr_kaynak;maliyet;satis_fiyati;komisyon;kargo;not
```

| Sütun | Ne yazılır |
|---|---|
| `ad` | Ürünün **Türkçe** adı: ürün türü ve ayırt edici özelliği (ör. "U şeklinde hamile yastığı"). Aynı türden birkaç ürün varsa ayırt etmek için sonuna parantez içinde marka ya da özellik ekle: "U şeklinde hamile yastığı (Momcozy, 145 cm)". Türkiye aramaları parantezsiz kısımla yapılır |
| `kategori` | Alt ürün türü (risk uyarıları ad ve kategoriye göre üretilir) |
| `marka` | Yalnızca herkesin bildiği büyük bir markanın ürünüyse (ör. Stanley, Medela). Sıradan satıcı adını buraya yazma; zaten `orijinal_ad`da görünür |
| `orijinal_ad` | **Ürünün kaynak sayfada yazan tam adı**, olduğu dilde. Her üründe doldur; araç "ürünü gör" bağlantılarını bundan kurar |
| `cince_ad` | Ürün türünün Çince arama terimi (F). 1688 ve Taobao araması bundan kurulur |
| `urun_link` | Ürünün kendi satış sayfası. Kaynak ASIN gösteriyorsa `https://www.amazon.com/dp/<ASIN>`. Görmediysen boş |
| `gorsel` | Ürün fotoğrafının `https://` ile başlayan adresi, kaynak sayfada gördüysen. Görmediysen boş; uydurma |
| `yurtdisi_fiyat` | Kaynakta görülen fiyat, para birimiyle (`$32.99`, `£6.45`) |
| `tedarik_fiyat`, `tedarik_moq`, `tedarikci`, `tedarik_link` | Çin'de üretici liste fiyatı aralığı, en az sipariş, üretici sayısı ve illeri, bakılan sayfa (F) |
| `ulke` | Satış rakamlarının ait olduğu ülke (ABD, İngiltere) |
| `kaynak` | Ürünü gördüğün sayfaların tam bağlantıları, aralarında boşluk |
| `kaynak_tarihi` | Her kaynak için sırayla yayın tarihi (`2026-09-20`), aralarında boşluk. **Yalnızca D türü yazılar için**; satış raporu, liste ya da mağaza sayfası için `-` |
| `satis_sirasi` | **Yalnızca** pazaryerinin kategori çok satanlar sırası (C). Anahtar kelime ya da haftalık liste sırası buraya yazılmaz |
| `yorum` | Satış sayfasındaki yorum ya da değerlendirme sayısı |
| `son_satis`, `son_satis_gun` | Son dönemde satılan adet ve o dönemin kaç gün olduğu (`10000` ve `30`; `1760` ve `7`). İkisi birlikte yazılır |
| `toplam_satis` | Bugüne kadar satılan toplam adet (yalnızca kaynak veriyorsa) |
| `satis_degisim` | Satışın bir önceki aya göre yüzde değişimi (`33.3`, `-12`) |
| `veri_tarihi` | Satış rakamlarının ait olduğu tarih (`2026-10-01`; yalnızca ay biliniyorsa `2026-07`). Sayfada tarih yoksa boş |
| `izlenme` | Video izlenmesi, gördüysen; puana girmez |
| `trend` | `yükseliyor`, `düz` ya da `düşüyor`; görmediysen boş |
| `not` | Kısa açıklama: listedeki satıcı, rozet, listelenme tarihi, "Fastest Growing bloğunda", emin olmadığın nokta |

`tr_` ile başlayan sütunları ve `maliyet`, `satis_fiyati`, `komisyon`, `kargo` sütunlarını ilk raporda
boş bırak (bkz. 6. adım). Sayılar `1760`, `1.76K`, `25.1K`, `2,4 milyon` biçiminde yazılabilir.

Bir satırdaki satış rakamları tek bir kaynaktan gelsin: bir ürünün satış adedini başka bir ürünün yorum
sayısıyla aynı satıra koyma.

## 5. Adım: Raporu üret ve aktar

`ARAC`, bu SKILL.md dosyasının bulunduğu klasördür. Çıktıları kullanıcıya dosya verebildiğin yazılabilir
klasöre yaz (aşağıda `CIKTI`; ör. Claude'da `/mnt/user-data/outputs`, ChatGPT'de `/mnt/data`).

```bash
python3 ARAC/agent.py tara CIKTI/urunler.csv --alan "Hamilelik ürünleri" \
  --rapor CIKTI/urun-raporu.html --excel CIKTI/urun-raporu.xlsx \
  --acilmayan "amazon.com, tiktok.com"

# Aracın çalıştığını göstermek için (örnek, uydurma veri)
python3 ARAC/agent.py tara ARAC/ornek/ornek_adaylar.csv --alan "Mutfak ürünleri" --tarih 2026-10-12
```

`--acilmayan`a yalnızca engellendiği için açamadığın siteleri yaz (404 veren ya da boş çıkan sayfaları
değil). Çıktıdaki "ÇİN'DE TEDARİK" bölümünde `Eksik:` satırı varsa ve o ürün türleri için F'ye hiç
bakmadıysan **F'ye dön, tamamla ve komutu yeniden çalıştır**. Komut çıktısında yalnızca öne çıkan ürünlerin ayrıntısı yazar; bütün ürünler bağlantılarıyla
rapor sayfasında ve Excel dosyasındadır.

**İki dosyayı da** indirilebilir olarak ver: `urun-raporu.html` asıl rapordur (tarayıcıda açılır;
ürünlerin fotoğrafı, bağlantıları ve Türkiye araması içindedir), `urun-raporu.xlsx` hesap içindir.

Kullanıcının dosyayı açmadan da sonucu görebilmesi için **sohbette ürünleri listele**:

1. **Yükselenler** tablosu (en fazla 15 ürün): ürün (Türkçe adı), listedeki adı, yurt dışı fiyatı, Çin'de
   üretici liste fiyatı, aylık satış, değişim ya da son 30 günün payı, **ürün bağlantısı**. Bağlantıyı tıklanabilir yaz:
   `[Ürünü aç](https://www.amazon.com/dp/...)`. Ürün sayfası yoksa aracın ayrıntıda yazdığı "Görseller"
   adresini `[Görsellere bak](...)` diye ver. **Bağlantısız ürün satırı yazma.**
2. **Çok satanlar** tablosu (en fazla 15 ürün): aynı sütunlar.
3. **Çin'de tedarik** tablosu (ürün türü başına bir satır; aracın "ÇİN'DE TEDARİK" çıktısından): ürün
   türü, Çince adı, yurt dışı fiyatı, Çin'de fabrika liste fiyatı, en az sipariş, tedarikçi illeri ve
   fiyatı gördüğün sayfanın bağlantısı. Fiyat bulamadığın türleri de "bakıldı, bulunamadı" diye yaz.
4. **Yazılarda geçenler**: tek satırda adlar ve kaç yazıda geçtiği.
5. Her bölümün altında bir cümle: bu liste hangi kaynağa ve hangi tarihe dayanıyor.

Sonra:

- Yükselenlerde kanıt düzeyini söyle; "zayıf" tek bir işarete dayandığını gösterir.
- Satış adetlerinin tahmin olduğunu ve rakamların tarihini söyle.
- Çin tarafını açık anlat: 1688, Taobao ve benzeri siteleri okuyamadığını; raporda her ürün için bu
  sitelerde arama bağlantısı olduğunu; fabrika fiyatının liste fiyatı olduğunu ve neyi içermediğini.
- Çok satanların çoğu yerleşik büyük markalardır ve aynısı getirilemez; bunu söyle ve satıcıyı aynı
  türün markasız ya da küçük satıcılı ürünlerine yönlendir.
- **Kendi gözlemini ekle, ama aracın sonucundan ayırarak** ("Benim notum:" diye): ürün büyük bir
  markaya özgü görünüyor, başka bir ürünün benzeri olabilir, rakam şüpheli duruyor, liste tek bir türe
  yığılmış. Aracın puanını ve sınıfını değiştirme.
- Risk uyarısı çıkan üründe uyarıyı öne al. Uyarılar kelime eşleşmesiyle üretilir; ürüne uymayan ya da
  eksik kalan bir uyarı görürsen söyle. Uyarı çıkmaması ürünün serbest olduğunu göstermez.
- Kaç alt ürün türüne baktığını, hangi kaynakların açılmadığını ve raporun neyi göremediğini söyle.

Kullanıcı ürün listesini kendisi verdiyse (yapıştırdı ya da dosya yükledi) 2. adımı atla, verdiği
rakamları aynı biçimde CSV'ye çevir. Onun vermediği rakamı sen ekleme.

## 6. Adım: Türkiye, kâr ve karar (kullanıcı isterse)

Türkiye'deki büyük pazaryerleri sana çoğu zaman açılmaz; zorlamadan geç. Rapordaki "Türkiye kontrolü"
bölümünde her ürün için tek tıkla Trendyol, Hepsiburada ve Google Trends araması vardır; kullanıcı
oradan bakar. Beğendiği ürünler için şunları iste:

- Pazaryerinde ilk sayfada **gerçekten aynı ürün** olan kaç ilan var (yoksa 0) ve tipik fiyatı (TL)
- Ürünün ona toplam maliyeti (TL) ve planladığı satış fiyatı
- O kategorideki komisyon oranı ve sipariş başına kargo masrafı (bilmiyorsa serinin ilk aracı, Pazar
  ve Komisyon Analizcisi, komisyonu verir)
- İsterse Google Trends'te (Türkiye, son 12 ay) eğrinin yönü

Verdiklerini CSV'ye işle: `tr_satici`, `tr_fiyat`, `maliyet`, `satis_fiyati`, `komisyon`, `kargo`,
`trend`. Sayıyı kullanıcı kendi gördüyse `tr_kontrol` sütununa `satıcı` yaz. Türkiye'de bir sayfayı sen
açabildiysen sayıyı yazabilirsin, ama `tr_kontrol`e `asistan` yaz ve bağlantıyı `tr_kaynak`a koy; araç
bunu kaba ipucu sayar ve ürünü "öncelikli" yapmaz. Bakılmadıysa boş bırak; `0` yalnızca arandı ve
bulunamadı demektir. CSV'de doğru satırı ürünün `ad`ına bakarak bul; raporun sırası CSV'nin sırası
değildir. Sonra aynı komutu yeniden çalıştır (komisyon ve kargo bütün ürünlerde aynıysa
`--komisyon 18 --kargo 60`). Karar tablosunda yalnızca bilgi girilen ürünler görünür.

## Araç ne hesaplar

- **Satış gücü (0-100):** kategori satış sırası, 30 güne oranlanmış satış adedi, yorum sayısı, toplam
  satış adedi. 50 ve üstü çok satan.
- **Çin'de tedarik:** hesaplamaz, toplar. Girdiğin Çince adı ve fabrika fiyatını ürün türüne göre tek
  tabloda gösterir, yurt dışı fiyatının yanına koyar, 1688 ve Taobao (Çince adla), Alibaba, AliExpress,
  Made-in-China ve Temu (listedeki adla) arama bağlantılarını kurar. Fabrika fiyatından kâr hesaplamaz.
- **Yükseliş (0-100):** satışın ne kadarının son 30 güne ait olduğu (toplam satış yoksa satış ÷ yorum);
  satışın bir önceki aya göre artışı; son 120 günde ürünü anlatan yazıların kaç ayrı sitede çıktığı;
  arama ilgisinin yönü. 60 ve üstü yükselen; bunun için satış rakamı şarttır.
- Küçük rakamlar ölçülmez: toplam satışı 10.000 adedin ya da aylık satışı 2.000 adedin altındaki üründe
  yükseliş hesaplanmaz. 120 günden eski satış rakamı da yükseliş sayılmaz. Yorumuna göre çok satan ürün
  "yeni" sayılır, ama artış rakamı olmadan yükselen sayılmaz.
- Görülemeyen işaret puanı düşürmez, "kanıt" düzeyini düşürür.
- **Sınıf:** çok satan ve yükselen · yeni yükselen · yükseliş adayı (yazılarda geçiyor, satış rakamı
  yok) · çok satan · öne çıkmadı · kanıt yetersiz.
- **Türkiye'de rekabet:** bulunamadı (0), az satıcı (1-5), orta (6-20), kalabalık (21+).
- **Kâr:** satış fiyatı − maliyet − komisyon − kargo. KDV, gelir vergisi, iade ve reklam dahil değildir.
- **Karar:** *öncelikli* (çok satan ya da yükselen; satıcının baktığı pazaryerinde satan yok ya da az;
  kâr marjı en az %20; yasaklı ya da izne bağlı değil), *incelenebilir*, *elenir* (zarar ya da yasak).

## Sınırlar

- Rapor, o gün açılabilen sayfalarla sınırlıdır; pazarın tamamını göstermez ve her taramada değişebilir.
- Pazaryeri satış adetleri üçüncü taraf sitelerin tahminidir; kaynak başına yalnızca ilk 10 ürün görülür.
- Rakamlar çoğunlukla ABD ve İngiltere pazarına aittir ve tarihleri birkaç ay eski olabilir.
- Ürünlerin bir kısmı markalı ya da tek satıcıya özgüdür; aynısı getirilemeyebilir.
- Yükseliş puanı ilginin göstergesidir; satış tahmini değildir.
- Çin'in iç pazar siteleri (1688, Taobao, JD, Pinduoduo, Douyin) okunamaz; rapor bunlar için arama
  bağlantısı verir. Fabrika fiyatı üretici dizinindeki liste fiyatıdır.
- Gümrük vergisi, ithalat izni ve belge koşulları hesaplanmaz; risk uyarıları genel bilgidir.
- Araç herhangi bir pazaryeriyle ya da sosyal medya platformuyla bağlantılı değildir.

Geliştiren: Harun Gökce — harungokce70@gmail.com — MIT lisansı
