---
name: satis-bolge-analizcisi
description: Türkiye'deki e-ticaret satıcıları için sipariş listesinden satışların coğrafi dağılımını çıkarır ve rapor hazırlar; il, bölge, ilçe ve mahalle bazında sipariş sayısı, ciro, ortalama sepet ve iade oranı, sayılara dayanan bulgular ve öneriler. Kullanıcı "satışlarım nereye gidiyor", "en çok hangi ile, hangi ilçeye satıyorum", "hangi bölgede güçlüyüm, nereye hiç satamıyorum", "reklamı hangi illere vermeliyim", "iade nereden geliyor" gibi sorular sorduğunda ya da sipariş dökümü yüklediğinde kullan. Sonucu rapor sayfası (HTML) ve Excel dosyası olarak verir.
---

# Satış Bölge Analizcisi

Bu klasördeki Python aracı, kullanıcının sipariş listesindeki il, ilçe ve mahalle sütunlarını sayar ve bir
**rapor** üretir: il, bölge, ilçe ve mahalle bazında sipariş sayısı, pay, ciro, ortalama sepet, iade oranı,
sipariş gelmeyen iller ve bu sayılara dayanan **bulgular ve öneriler**. Ek paket ve internet gerektirmez
(Python 3.10+ yeterli). Sayıları ve önerileri araç üretir; sen aktarır ve açıklarsın.

Bu klasör sana bir ZIP dosyası olarak verildiyse (ör. ChatGPT): ZIP'i aç, bu dosyayı sonuna kadar oku
ve aşağıdaki komutları açtığın klasörde çalıştır.

## Önce: sipariş listesi gerekli

Bu araç kullanıcının kendi sipariş listesiyle çalışır. Kullanıcı dosya eklemeden soru sorduysa aracı
çalıştırma ve örnek veriyle sonuç uydurma; ondan sipariş listesini istemen yeterli:

> Bunun için sipariş listeniz gerekiyor. Pazaryeri satıcı panelinizde Siparişler sayfasından listeyi Excel
> olarak indirin; müşteri adı, telefon ve açık adres sütunlarını silin (il, ilçe, mahalle, tutar, ürün,
> sipariş no ve durum kalsın) ve dosyayı mesaj kutusundaki + düğmesiyle buraya ekleyin.

Kullanıcı yalnızca aracın nasıl çalıştığını görmek isterse örnek dosyayı kullanabilirsin; o durumda
sonucun **örnek (uydurma) veri** olduğunu açıkça söyle.

## Kişisel veri

Sipariş dökümleri müşteri adı, telefon ve açık adres içerir. **Bu analiz için bunların hiçbiri gerekmez;
il, ilçe ve mahalle yeter.**

- Kullanıcı henüz dosya yüklemediyse, yüklemeden önce ad, telefon, e-posta, açık adres (sokak, kapı no)
  ve T.C. kimlik no sütunlarını silmesini söyle.
- Kullanıcı bu sütunları içeren bir dosya yüklediyse: bunu kısaca belirt, o sütunları **hiçbir çıktıya,
  ara dosyaya ya da yanıta taşıma** ve analiz için hazırladığın CSV'ye yalnızca gerekli sütunları yaz.
- İl, ilçe ya da mahalle ayrı sütun değil de tek bir adres metninin içindeyse: o metinden yalnızca il,
  ilçe ve mahalle adını ayır ve CSV'ye yalnızca bu üçünü yaz; sokak, kapı numarası ve kişi adı CSV'ye
  girmesin. Ayıramadığın satırda uydurma; hücreyi boş bırak.
- Tek tek müşterileri listeleme, bir kişinin siparişlerini çıkarma ya da adresleri gösterme. Bu araç
  toplu dağılım içindir. Araç, 3 siparişten azı olan mahalleleri zaten tek tek göstermez.

## Kurallar

1. **Sayıları kendin sayma ve tahmin yürütme.** Her adet, pay ve tutar aracın çıktısından gelsin.
   Aracı çalıştıramıyorsan sayı verme; çalıştıramadığını söyle.
2. Listeye sipariş ekleme, il, ilçe ya da mahalle tahmin etme. İli yazmayan ya da tanınmayan satırlar
   analize girmez; araç bunların sayısını söyler, sen de aktar.
3. **Önerileri aracın çıktısından al.** "BULGULAR VE ÖNERİLER" bölümündeki her maddeyi, dayandığı sayıyla
   birlikte aktar. Kendi yorumunu eklersen bunun aracın değil senin yorumun olduğunu söyle ve listede
   olmayan bir sayıya dayandırma.
4. Her sonuçta şunu belirt: analiz yalnızca verilen sipariş listesini kapsar.

## Sipariş listesini hazırlama

Kullanıcının yüklediği dosyayı (Excel ya da CSV) şu sütunlarla bir CSV'ye çevir:

```
sipariş no;il;ilçe;mahalle;ürün;tutar;durum
1001;İstanbul;Kadıköy;Göztepe;Çelik Termos 500 ml;389,90;Teslim edildi
1002;Ankara;Çankaya;Ayrancı;Termos Kupa;279,90;İade edildi
```

- Zorunlu sütun yalnızca `il`dir. Diğerleri varsa rapor zenginleşir: `ilçe` → il içinde ilçe dağılımı,
  `mahalle` → ilçe içinde mahalle dağılımı, `tutar` → ciro ve ortalama sepet, `durum` → iade oranı,
  `ürün` → illerde en çok satan ürün.
- Dosyada birden fazla il sütunu varsa (teslimat ili, fatura ili) **teslimat ilini** kullan; emin
  değilsen kullanıcıya sor.
- `durum` içinde "iade" geçen satırlar iade, "iptal" geçenler iptal sayılır; iptaller analize girmez.
- Aynı sipariş numarası birden çok satırda geçiyorsa (sepette birden çok ürün) bir sipariş sayılır.
- İl ve mahalle adlarını düzeltmene gerek yok; araç yazım farklarını (İSTANBUL, istanbul, Urfa, K.Maraş;
  "Atakent Mah.", "ATAKENT MAHALLESİ") tanır.
- En az 10 sipariş gerekir; 100 ve üzeri daha güvenilirdir.

## Çalıştırma

`ARAC`, bu SKILL.md dosyasının bulunduğu klasördür. Çıktıları kullanıcıya dosya verebildiğin yazılabilir
klasöre yaz (aşağıda `CIKTI`; ör. Claude'da `/mnt/user-data/outputs`, ChatGPT'de `/mnt/data`).

```bash
python3 ARAC/agent.py analiz CIKTI/siparisler.csv \
  --rapor CIKTI/satis-bolge-raporu.html --excel CIKTI/satis-bolge-analizi.xlsx

# Yalnızca aracın nasıl çalıştığını göstermek için (örnek, uydurma veri)
python3 ARAC/agent.py analiz ARAC/ornek/ornek_siparisler.csv --rapor CIKTI/ornek-rapor.html
```

`--baslik "..."` ile rapor sayfasına başlık verebilirsin (ör. mağaza adı ve dönem); `--tarih YYYY-AA-GG`
rapor tarihini belirler.

## Sonucu kullanıcıya aktarma

**Asıl çıktı rapor sayfasıdır (HTML).** Kullanıcı raporu sohbetin yanındaki panelde açık görmek ister:

- Aracın ürettiği `satis-bolge-raporu.html` dosyasını **olduğu gibi** kullanıcıya dosya olarak sun; Claude'da
  dosya `/mnt/user-data/outputs` altında olmalı ve dosya sunma aracıyla verilmelidir, böylece yan panelde
  açılır. **Önce rapor sayfasını, ardından Excel dosyasını sun** (ilk sunulan dosya panelde açılır).
- Raporu kendin yeniden yazma, HTML'ini değiştirme ya da içeriğini baştan bir sayfaya dökme; araç zaten
  hazır, tek dosyalık ve internete bağlanmayan bir sayfa üretir.
- Dosya sunulamıyorsa bunu söyle ve dosyanın yolunu ver.

Dosyaları sunduktan sonra sohbette kısa bir özet yaz:

1. **Genel tablo:** kaç sipariş, kaç il, ilk 3 ilin payı.
2. **İl → ilçe → mahalle:** ilk 3 il için aracın "… İÇİNDE İLÇELER VE MAHALLELER" bölümünü tablo olarak
   ver: ilçe, sipariş, ildeki payı, öne çıkan mahalleler. Yalnızca il sıralaması verip bırakma.
3. **Bulgular ve öneriler:** aracın yazdığı her maddeyi sırasıyla aktar: konu, dayandığı sayı, öneri.
   Madde atlamak ya da sayısını değiştirmek yok.
4. **Sınır:** analiz yalnızca bu listeyi kapsar; iade oranı ve ortalama sepet az siparişli yerlerde
   yanıltıcıdır (araç bunları en az 20 siparişli yerlerde yorumlar).

Bir ilin payının yüksek olması orada talebin yüksek olduğunu tek başına göstermez; nüfus da etkiler.
Araç nüfus sayısı içermez; yalnızca "nüfusu en kalabalık 10 il" sıralamasını (TÜİK 2023) sipariş
gelmeyen büyük illeri bulmak için kullanır.

Mahalle sütunu yoksa rapor mahalle bölümünü çıkarmaz; bunu kullanıcıya söyle ve dökümünde mahalle
bilgisi varsa onu da ekleyerek yeniden deneyebileceğini belirt.

## Araç ne hesaplar

- **Dağılım:** bölge, il, ilçe, mahalle bazında sipariş sayısı, pay, ciro, ortalama sepet, iade oranı;
  her yerde en çok satan ürün; sipariş gelmeyen iller.
- **Bulgular ve öneriler** sabit kurallarla üretilir (eşikler README'de): ilk üç ilin payı, büyük illerde
  ilçe yoğunlaşması, öne çıkan mahalleler, baskın bölge (kargo), ortalamanın belirgin üstünde ya da altında
  sepet, yüksek ya da sıfır iade, sipariş gelmeyen kalabalık iller, öne çıkan ürünü farklı olan iller.
- Araç nüfus, mevsim, reklam harcaması ya da kâr bilmez; öneriler denenecek adımlardır, sonuç sözü değildir.

## Sınırlar

- Sonuçlar verilen listeyle sınırlıdır. Tek bir ayın siparişleri mevsim etkisi taşıyabilir.
- Araç adres çözümlemez; il, ilçe ve mahalle listedeki sütunlardan olduğu gibi alınır.
- Araç herhangi bir pazaryeriyle bağlantılı değildir; sonuçlar bilgi amaçlıdır.

Geliştiren: Harun Gökce — harungokce70@gmail.com — MIT lisansı
