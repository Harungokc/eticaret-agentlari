---
name: reklam-analizcisi
description: Türkiye'deki e-ticaret satıcıları için reklam raporundan (Trendyol, Hepsiburada, Amazon, Meta, Google ya da başka bir panelden indirilen) hangi reklamın satış getirdiğini, hangisinin bütçeyi boşa harcadığını çıkarır; ürün maliyeti verilirse reklamdan sonra elde kalan kârı ve başa baş noktasını hesaplar; sayılara dayanan bulgular ve öneriler. Kullanıcı "reklam kâr ettiriyor mu", "reklam bütçem nereye gidiyor", "hangi ürüne reklam vermeliyim", "ROAS'ım iyi mi", "hangi arama terimleri para yakıyor" gibi sorular sorduğunda ya da reklam raporu yüklediğinde kullan. Sonucu rapor sayfası (HTML) ve Excel dosyası olarak verir.
---

# Reklam Analizcisi

Bu klasördeki Python aracı, kullanıcının reklam raporunu ürün (ya da kampanya) ve arama terimi bazında toplar
ve bir **rapor** üretir: harcama, reklamdan gelen satış, reklam getirisi (ROAS), reklam maliyet oranı, tıklama
oranı, dönüşüm; maliyet bilgisi verilirse **reklamdan sonra elde kalan** ve **başa baş oranı**; bu sayılara
dayanan **bulgular ve öneriler**. Ek paket ve internet gerektirmez (Python 3.10+ yeterli). Sayıları ve önerileri
araç üretir; sen aktarır ve açıklarsın.

Bu klasör sana bir ZIP dosyası olarak verildiyse (ör. ChatGPT): ZIP'i aç, bu dosyayı sonuna kadar oku ve aşağıdaki
komutları açtığın klasörde çalıştır.

## Önce: reklam raporu gerekli

Araç kullanıcının kendi reklam raporuyla çalışır. Kullanıcı dosya eklemeden soru sorduysa aracı çalıştırma ve
örnek veriyle sonuç uydurma; raporu iste:

> Bunun için reklam raporunuz gerekiyor. Satıcı panelinizin reklam bölümünden, ürün bazında (varsa arama terimi
> bazında) raporu Excel ya da CSV olarak indirin ve mesaj kutusundaki + düğmesiyle buraya ekleyin. Reklamın kâr
> ettirip ettirmediğini de görmek isterseniz ürünlerinizin birim maliyetini, komisyon oranını ve kargo ücretini de
> yazın ya da bir tablo olarak ekleyin.

Kullanıcı yalnızca aracın nasıl çalıştığını görmek isterse örnek dosyaları kullanabilirsin; o durumda sonucun
**örnek (uydurma) veri** olduğunu açıkça söyle.

## Kurallar

1. **Sayıları kendin hesaplama ve tahmin yürütme.** Her tutar, oran ve kâr aracın çıktısından gelsin. Aracı
   çalıştıramıyorsan sayı verme; çalıştıramadığını söyle.
2. **Maliyet uydurma.** Kullanıcı ürün maliyetini, komisyonu ya da kargoyu vermediyse bunları tahmin etme;
   aracı maliyetsiz çalıştır ve kârın hesaplanmadığını söyle. Kullanıcı yalnızca "kâr payım yaklaşık %25" gibi
   genel bir oran verirse `--kar-marji 25` kullan.
3. **Önerileri aracın çıktısından al.** "BULGULAR VE ÖNERİLER" bölümündeki her maddeyi dayandığı sayıyla birlikte
   aktar. Kendi yorumunu eklersen bunun aracın değil senin yorumun olduğunu söyle.
4. Araç reklam hesabına bağlanmaz ve hiçbir değişiklik yapmaz. Kullanıcı "reklamı durdur, teklifi değiştir"
   derse bunu panelden kendisinin yapması gerektiğini söyle.
5. Her sonuçta şunu belirt: panelin gösterdiği reklam satışı, reklam olmasa da gelecek satışları ayırmaz; reklam
   getirisi gerçek etkiden yüksek görünebilir.

## Sütunları denetleme (her yeni dosyada önce bunu yap)

Pazaryerlerinin reklam raporlarında sütun adları farklıdır ve değişebilir. Önce eşleştirmeye bak:

```bash
python3 ARAC/agent.py sutunlar KULLANICININ_DOSYASI.xlsx
```

Çıktı, dosyadaki sütunları ve aracın hangisini **ürün, kampanya, arama terimi, harcama, satış tutarı, sipariş,
tıklama, gösterim** olarak aldığını gösterir.

- **Harcama** ve **ürün / kampanya / arama terimi** sütunlarından biri zorunludur. Satış tutarı yoksa getiri ve
  kâr hesaplanmaz; sipariş yoksa dönüşüm hesaplanmaz.
- Bir alan "(bulunamadı)" görünüyor ama dosyada karşılığı açıkça varsa `--sutun` ile eşle:
  `--sutun harcama="Harcanan Tutar" --sutun ciro="Reklam Satışı"`. Alan adları: `urun`, `kampanya`, `terim`,
  `harcama`, `ciro` (satış tutarı), `siparis`, `tiklama`, `gosterim`.
- **Yanlış eşleşmeye dikkat:** "satış" adlı sütun adet de olabilir tutar da. Değerlere bakarak karar ver; emin
  değilsen kullanıcıya sor. Bir sütunun ne olduğunu tahmin ederek eşleme.
- Eşleştirmeyi kullanıcıya bir satırla söyle (ör. "Harcama: 'Harcama (TL)', satış: 'Satış Tutarı (TL)'").
- Dosyanın başında açıklama satırları ya da altında toplam satırı olabilir; araç bunları tanır.

## Maliyet bilgisi

Reklamın kâr ettirip ettirmediği için ürün başına reklam öncesi kâr gerekir. Kullanıcı verdiyse şu sütunlarla
bir CSV hazırla (ürün adları reklam raporundaki gibi yazılmalı):

```
Ürün;Birim maliyet;Komisyon (%);Kargo;Satış fiyatı
Çelik Termos 500 ml;190;20;45;389,90
```

- Komisyon yüzde olarak yazılır (20 = %20). Satış fiyatı boşsa araç reklamdan gelen satış ÷ sipariş alır.
- Raporda olup maliyet tablosunda olmayan ürünlerin kârı hesaplanmaz; araç bunları listeler, sen de aktar.

## Çalıştırma

`ARAC`, bu SKILL.md dosyasının bulunduğu klasördür. Çıktıları kullanıcıya dosya verebildiğin yazılabilir klasöre
yaz (aşağıda `CIKTI`; ör. Claude'da `/mnt/user-data/outputs`, ChatGPT'de `/mnt/data`).

```bash
python3 ARAC/agent.py analiz KULLANICININ_DOSYASI.xlsx --maliyet CIKTI/maliyetler.csv \
  --rapor CIKTI/reklam-raporu.html --excel CIKTI/reklam-analizi.xlsx

# Maliyet tablosu yok ama genel kâr payı biliniyorsa
python3 ARAC/agent.py analiz KULLANICININ_DOSYASI.xlsx --kar-marji 25 --rapor CIKTI/reklam-raporu.html

# Yalnızca aracın nasıl çalıştığını göstermek için (örnek, uydurma veri)
python3 ARAC/agent.py analiz ARAC/ornek/ornek_urun_reklami.csv --maliyet ARAC/ornek/ornek_maliyetler.csv \
  --rapor CIKTI/ornek-rapor.html
```

`--baslik "..."` ile rapor sayfasına başlık verebilirsin (ör. mağaza adı ve dönem); `--tarih YYYY-AA-GG` rapor
tarihini belirler.

## Sonucu kullanıcıya aktarma

**Asıl çıktı rapor sayfasıdır (HTML).** Aracın ürettiği `reklam-raporu.html` dosyasını **olduğu gibi** dosya olarak
sun (Claude'da `/mnt/user-data/outputs` altında, dosya sunma aracıyla; böylece yan panelde açılır). **Önce rapor
sayfasını, ardından Excel dosyasını sun.** Raporu kendin yeniden yazma ya da HTML'ini değiştirme. Dosya
sunulamıyorsa bunu söyle ve dosyanın yolunu ver.

Dosyaları sunduktan sonra sohbette kısa bir özet yaz:

1. **Genel tablo:** harcama, reklamdan gelen satış, ROAS; maliyet verildiyse **reklam sonrası kalan**. Panel ROAS'ı
   iyi görünüp reklam sonrası kalan eksiyse bunu açıkça söyle; raporun asıl bulgusu budur.
2. **Bulgular ve öneriler:** aracın yazdığı her maddeyi sırasıyla aktar: konu, dayandığı sayı, öneri. Madde
   atlamak ya da sayısını değiştirmek yok.
3. **Sınır:** analiz yalnızca bu raporu kapsar; reklam satışı reklamsız gelecek satışı ayırmaz; kâr, verilen
   maliyet bilgisi kadar doğrudur.

## Araç ne hesaplar

- **Oranlar:** ROAS (satış ÷ harcama), reklam maliyet oranı (harcama ÷ satış), tıklama oranı, dönüşüm (sipariş ÷
  tıklama), tıklama başı ve sipariş başı maliyet.
- **Kâr:** sipariş başına reklam öncesi kâr = satış fiyatı − ürün maliyeti − komisyon − kargo; başa baş oranı = bu
  kâr ÷ satış fiyatı (reklam maliyet oranı bunu aşarsa reklam zarar ettirir); reklam sonrası kalan = sipariş ×
  sipariş başına kâr − harcama.
- **Bulgular ve öneriler** sabit kurallarla üretilir: en az 20 tıklama alıp satış getirmeyen kalemler, harcama
  payı satış payını aşan yoğunlaşma, zarar ettiren ve rahat kâr ettiren reklamlar, reklamsız da zarar eden
  ürünler, tıklanmayan ve tıklanıp satmayan kalemler, satış getirmeyen, pahalı ve verimli arama terimleri.
  Kârlılık en az 3 siparişli kalemde, tıklama oranı en az 1.000 gösterimde yorumlanır.

## Sınırlar

- Sonuçlar verilen raporla ve pazaryerinin reklama bağladığı satışla sınırlıdır; atıf süresi platforma göre değişir.
- Araç mevsim, stok, rakip ya da reklam ayarlarını bilmez; öneriler denenecek adımlardır, sonuç sözü değildir.
- Araç herhangi bir pazaryeriyle ya da reklam hesabıyla bağlantılı değildir; sonuçlar bilgi amaçlıdır.

Geliştiren: Harun Gökce — harungokce70@gmail.com — MIT lisansı
