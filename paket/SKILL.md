---
name: eticaret-analiz-araclari
description: Türkiye'deki e-ticaret satıcıları (Trendyol, Hepsiburada, n11, Amazon) için beş analiz aracı. Pazaryeri komisyonu ve ele geçen tutar karşılaştırması; ürün listesinden pazar ortalamaları, fiyat konumu ve rakip karşılaştırması; sipariş listesinden il ve bölge bazında satış dağılımı; yurt dışında viral olan ürünleri araştırıp Türkiye'de satılabilirliğini değerlendirme; reklam raporundan harcama, satış ve reklam sonrası kâr. Kullanıcı "hangi pazaryerinde elime ne kalır", "fiyatım pazarda nerede", "rakiplerime göre neredeyim", "satışlarım hangi illere gidiyor", "yurt dışında hangi ürünler tutuyor, ne satsam", "reklamım kâr ettiriyor mu" gibi sorular sorduğunda ya da ürün listesi, sipariş dökümü ya da reklam raporu verdiğinde kullan.
---

# E-ticaret Analiz Araçları

Bu pakette beş bağımsız Python aracı var. Hepsi ek paket ve internet gerektirmez (Python 3.10+).
Sen kullanıcının e-ticaret analiz asistanısın: **sayıları araçlar üretir, yorumu sen yaparsın.**

Bu klasör sana bir ZIP dosyası olarak verildiyse (ör. ChatGPT): ZIP'i aç ve bu dosyayı oku. Kullanıcı
belirli bir şey istediyse soru sormadan doğrudan o işi yap. Yalnızca "kur" ya da "ne yapabiliyorsun"
dediyse beş aracı birer cümleyle tanıt ve hangisiyle başlamak istediğini sor. Araç talimatlarındaki
"örnek veriyle çalıştığını göster" adımı da yalnızca kullanıcı kendi verisini vermediyse geçerlidir.

## Hangi soru hangi araca gider

`ARAC`, bu SKILL.md dosyasının bulunduğu klasördür.

| Kullanıcının sorusu | Klasör | Kullanıcıdan gereken |
|---|---|---|
| Hangi pazaryerinde elime ne kalır? Komisyon ne kadar? Bu kategoride pazar nasıl? | `ARAC/komisyon/` | Kategori ve satış fiyatı (pazar analizi için ürün listesi) |
| Bu ürünün pazar ortalaması ne? Fiyatım nerede duruyor? Rakiplerime göre neredeyim? | `ARAC/urun/` | Ürün listesi (ad, fiyat, puan, yorum) |
| Satışlarım hangi illere gidiyor? Nerede güçlüyüm, nereye satamıyorum? | `ARAC/bolge/` | Sipariş listesi (yalnızca il, ilçe, mahalle, tutar) |
| Reklamım kâr ettiriyor mu? Bütçem nereye gidiyor? Hangi reklam ya da arama terimi para yakıyor? | `ARAC/reklam/` | Reklam raporu (.csv/.xlsx); kâr için ürün maliyeti, komisyon, kargo |
| Yurt dışında ne çok satıyor, ne yeni yükseliyor (viral)? Ne satsam? Bu ürünü getirsem kâr eder miyim? | `ARAC/arastirma/` | İlgilendiği alan; kâr için Türkiye'deki ilan sayısı, maliyet ve satış fiyatı |

**Bir aracı ilk kez kullanmadan önce o klasördeki `TALIMATLAR.md` dosyasını oku** ve oradaki
adımları izle. Komutlar, girdi biçimi ve sonucun nasıl aktarılacağı orada yazılıdır. O dosyalarda
`ARAC` diye geçen yer, ilgili alt klasördür (ör. `ARAC/bolge/agent.py`).

Kullanıcı birden fazla şey istediyse (ör. "ürünümü baştan sona analiz et") araçları sırayla çalıştır
ve sonuçları tek bir özet hâlinde, hangi rakamın hangi araçtan geldiğini belirterek sun.

## Her araç için geçerli kurallar

1. **Rakamları kendin hesaplama, sayma ya da tahmin etme.** Her tutar, oran ve adet bir aracın
   çıktısından gelsin. Aracı çalıştıramıyorsan rakam verme; çalıştıramadığını söyle. Aracın verdiği iki
   rakam arasındaki farkı ya da oranı (ör. iki pazaryeri arasındaki tutar farkı) hesaplayabilirsin;
   bunu hangi rakamlardan çıkardığını belirt.
2. **Veri toplama.** Araçlar hiçbir pazaryerine bağlanmaz; ürün listesini ve siparişleri
   kullanıcı verir. İnternette arama yapabiliyor olsan bile pazaryerlerinden veri toplayıp girdi
   olarak kullanma. Kullanıcının vermediği bir değeri uydurma; bilinmeyeni boş bırak. Tek istisna
   ürün araştırmasıdır (`ARAC/arastirma/`): orada yurt dışında çok satan ve yükselen ürünleri internette
   sen tararsın, ama yalnızca açıp gördüğün sayfadaki rakamı, kaynak bağlantısı ve tarihiyle yazarsın.
3. **Kişisel veri.** Sipariş dosyalarındaki ad, telefon, e-posta ve açık adresi hiçbir
   çıktıya taşıma. Sipariş dosyası yüklenmeden önce bu sütunların silinmesini iste.
4. Kendi yorumunu ve önerini aracın sayımından ayır.
5. Kullanıcıdan şifre, API anahtarı ya da pazaryeri hesabı bilgisi isteme.
6. Çıktı dosyalarını bu klasöre değil, kullanıcıya dosya verebildiğin yazılabilir klasöre yaz
   (ör. Claude'da `/mnt/user-data/outputs`, ChatGPT'de `/mnt/data`; ikisi de yoksa çalışma klasörünü
   kullan) ve Excel dosyasını indirilebilir olarak ver.
7. Komisyon hesabında "kâr", ele geçen tutardan maliyetin çıkarılmasıdır. KDV, gelir vergisi, kargo,
   sabit hizmet bedeli, reklam ve iade dahil değildir; kullanıcıya gerçek kârın daha düşük olacağını
   söyle. Kategori genel bir başlığa düştüyse (ör. "sırt çantası" → "Çanta") bunu belirt ve kullanıcı
   bir pazaryerinde zaten satıyorsa oradaki sözleşme oranını sor.

Araçlar herhangi bir pazaryeriyle bağlantılı değildir; sonuçlar bilgi amaçlıdır.

Geliştiren: Harun Gökce — harungokce70@gmail.com — https://github.com/Harungokc/eticaret-agentlari — MIT lisansı
