---
name: satis-bolge-analizcisi
description: Türkiye'deki e-ticaret satıcıları için sipariş listesinden satışların coğrafi dağılımını çıkarır; il, bölge ve ilçe bazında sipariş sayısı, ciro, ortalama sepet ve iade oranı. Kullanıcı "satışlarım nereye gidiyor", "en çok hangi ile satıyorum", "hangi bölgede güçlüyüm, nereye hiç satamıyorum", "reklamı hangi illere vermeliyim" gibi sorular sorduğunda ya da sipariş dökümü yüklediğinde kullan. Sonucu Excel dosyası olarak verir.
---

# Satış Bölge Analizcisi

Bu klasördeki Python aracı, kullanıcının sipariş listesindeki il ve ilçe sütunlarını sayar: il, bölge
ve ilçe bazında sipariş sayısı, pay, ciro, ortalama sepet, iade oranı ve sipariş gelmeyen iller. Ek
paket ve internet gerektirmez (Python 3.10+ yeterli). Sayıları araç üretir, yorumu sen yaparsın.

Bu klasör sana bir ZIP dosyası olarak verildiyse (ör. ChatGPT): ZIP'i aç, bu dosyayı sonuna kadar oku
ve aşağıdaki komutları açtığın klasörde çalıştır.

## Önce: kişisel veri

Sipariş dökümleri müşteri adı, telefon ve açık adres içerir. **Bu analiz için bunların hiçbiri
gerekmez; yalnızca il ve ilçe yeter.**

- Kullanıcı henüz dosya yüklemediyse, yüklemeden önce ad, telefon, e-posta, açık adres ve T.C. kimlik
  no sütunlarını silmesini söyle. Gerekli sütunlar: il, ilçe, tutar, ürün, sipariş no, durum.
- Kullanıcı bu sütunları içeren bir dosya yüklediyse: bunu kısaca belirt, o sütunları **hiçbir çıktıya,
  ara dosyaya ya da yanıta taşıma** ve analiz için hazırladığın CSV'ye yalnızca gerekli sütunları yaz.
- Tek tek müşterileri listeleme, bir kişinin siparişlerini çıkarma ya da adresleri gösterme. Bu araç
  toplu dağılım içindir.

## Kurallar

1. **Sayıları kendin sayma ve tahmin yürütme.** Her adet, pay ve tutar aracın çıktısından gelsin.
   Aracı çalıştıramıyorsan sayı verme; çalıştıramadığını söyle.
2. Listeye sipariş ekleme, il tahmin etme. İli yazmayan ya da tanınmayan satırlar analize girmez;
   araç bunların sayısını söyler, sen de aktar.
3. Her sonuçta şunu belirt: analiz yalnızca verilen sipariş listesini kapsar.

## Sipariş listesini hazırlama

Kullanıcının yüklediği dosyayı (Excel ya da CSV) şu sütunlarla bir CSV'ye çevir:

```
sipariş no;il;ilçe;ürün;tutar;durum
1001;İstanbul;Kadıköy;Çelik Termos 500 ml;389,90;Teslim edildi
1002;Ankara;Çankaya;Termos Kupa;279,90;İade edildi
```

- Zorunlu sütun yalnızca `il`dir. Diğerleri varsa analiz zenginleşir: `tutar` → ciro ve ortalama
  sepet, `durum` → iade oranı, `ürün` → illerde en çok satan ürün, `ilçe` → ilçe sıralaması.
- Dosyada birden fazla il sütunu varsa (teslimat ili, fatura ili) **teslimat ilini** kullan; emin
  değilsen kullanıcıya sor.
- `durum` içinde "iade" geçen satırlar iade, "iptal" geçenler iptal sayılır; iptaller analize girmez.
- Aynı sipariş numarası birden çok satırda geçiyorsa (sepette birden çok ürün) bir sipariş sayılır.
- İl adlarını düzeltmene gerek yok; araç yazım farklarını (İSTANBUL, istanbul, Urfa, K.Maraş) tanır.
- En az 10 sipariş gerekir; 100 ve üzeri daha güvenilirdir.

## Çalıştırma

`ARAC`, bu SKILL.md dosyasının bulunduğu klasördür. Çıktıları kullanıcıya dosya verebildiğin yazılabilir
klasöre yaz (aşağıda `CIKTI`; ör. Claude'da `/mnt/user-data/outputs`, ChatGPT'de `/mnt/data`).

```bash
python3 ARAC/agent.py analiz CIKTI/siparisler.csv --excel CIKTI/satis-bolge-analizi.xlsx

# Aracın çalıştığını göstermek için (örnek, uydurma veri)
python3 ARAC/agent.py analiz ARAC/ornek/ornek_siparisler.csv
```

## Sonucu kullanıcıya aktarma

1. **Genel tablo:** kaç sipariş, kaç il, ilk 3 ilin payı (satışlar ne kadar yoğunlaşmış).
2. **Güçlü bölgeler ve iller:** ilk 5 il, sipariş payı ve varsa ciro ile.
3. **Dikkat çekenler:** ortalama sepeti ya da iade oranı diğerlerinden belirgin farklı olan iller.
   İade oranını yalnızca en az 20 siparişi olan iller için yorumla.
4. **Boşluklar:** sipariş gelmeyen ya da çok az gelen büyük iller.
5. **Ne yapılabilir:** reklam hedeflemesi, kargo anlaşması, stok ya da kampanya için birkaç somut
   öneri. Bunları kendi önerin olarak sun; aracın hesabı gibi gösterme.

Bir ilin payının yüksek olması orada talebin yüksek olduğunu tek başına göstermez; nüfus da etkiler.
İstanbul'un ilk sırada çıkması çoğu zaman beklenen bir sonuçtur, bunu belirt. Araç nüfus verisi
içermez; nüfusa oranla karşılaştırma yapacaksan bunun kendi bilgin olduğunu söyle.

Excel dosyasını indirilebilir dosya olarak ver. Google Sheets'te açmak için: **Dosya > İçe aktar >
Yükle**.

## Sınırlar

- Sonuçlar verilen listeyle sınırlıdır. Tek bir ayın siparişleri mevsim etkisi taşıyabilir.
- Araç adres çözümlemez; il ve ilçe, listedeki sütunlardan olduğu gibi alınır.
- Araç herhangi bir pazaryeriyle bağlantılı değildir; sonuçlar bilgi amaçlıdır.

Geliştiren: Harun Gökce — harungokce70@gmail.com — MIT lisansı
