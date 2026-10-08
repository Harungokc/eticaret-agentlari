# Pazar ve Komisyon Analizcisi

E-ticaret satıcıları için iki soruya cevap veren açık kaynak bir analiz aracı:

1. **Bu pazarda durum ne?** Bir ürün listesinden fiyat bantlarını, öne çıkan markaları, rekabet
   yoğunluğunu ve boş kalan fiyat aralıklarını çıkarır.
2. **Hangi pazaryerinde elime ne kalır?** Kategori ve fiyata göre Trendyol, Hepsiburada, n11 ve
   Amazon Türkiye komisyonlarını karşılaştırır.

İkisi birlikte çalışır: pazar analizinin bulduğu ortanca fiyat, komisyon karşılaştırmasına girer.

## Kurulum

Python 3.10 veya üstü yeterli; ek paket gerekmez.

```bash
git clone https://github.com/Harungokc/eticaret-agentlari.git
cd eticaret-agentlari/01-pazar-ve-komisyon-analizcisi
python agent.py pazar ornek/ornek_urunler.csv --kategori "erkek parfüm"
```

## Kullanım

### Komisyon karşılaştırması

```bash
python agent.py komisyon "kadın ayakkabı" 899
python agent.py komisyon "telefon kılıfı" 249 --maliyet 80      # kârı da hesaplar
python agent.py komisyon giyim 599 --trendyol 21.5              # kendi sözleşme oranınızla
python agent.py kategoriler                                     # tablodaki kategoriler
```

```
Pazaryeri       Komisyon oranı  Komisyon               Ele geçen              Kâr
--------------  --------------  ---------------------  ---------------------  ---------------------
Hepsiburada     %18 – %19,49    161,82 TL – 175,22 TL  723,78 TL – 737,18 TL  323,78 TL – 337,18 TL
n11             %15 – %20,34    134,85 TL – 182,86 TL  698,16 TL – 746,17 TL  298,16 TL – 346,17 TL
Trendyol        %21,5 – %22,5   193,28 TL – 202,28 TL  696,72 TL – 705,72 TL  296,72 TL – 305,72 TL
```

### Pazar analizi

```bash
python agent.py pazar urunler.csv
python agent.py pazar urunler.csv --kategori "erkek parfüm" --maliyet 150
python agent.py pazar arama-sayfasi.html --kategori kozmetik
```

Ürün listesini üç biçimde verebilirsiniz:

| Biçim | Nasıl hazırlanır |
|---|---|
| `.csv` | Sütunlar: `ad, marka, fiyat, puan, yorum` (yalnızca `fiyat` zorunlu). Virgül veya noktalı virgül ayırıcı, `1.299,90` biçimi kabul edilir. |
| `.json` | Aynı alanları taşıyan bir ürün dizisi. |
| `.html` | Tarayıcınızda açtığınız arama sayfasını "Farklı kaydet → Web sayfası, tamamı" ile kaydedin. |

`ornek/ornek_urunler.csv` denemeniz için konmuş, tamamen uydurma bir listedir; gerçek marka, ürün
veya fiyat içermez.

Rapor şunları içerir: fiyat özeti (en düşük, çeyrekler, ortanca, en yüksek), fiyat bantları, öne
çıkan markalar, ortanca puan ve yorum, en çok yorumlanan 10 ürünün toplam yorumdaki payı ve varsa az
rakipli ama ilgi gören fiyat bandı.

## Bilmeniz gereken sınırlar

- **Komisyon oranları yaklaşıktır.** Pazaryerleri oranları herkese açık tek bir resmi tabloda
  yayımlamıyor; bağlayıcı oran satıcı panelinizdeki sözleşme ekranındadır. `veri/komisyon.json`
  içindeki değerler e-ticaret yazılım firmalarının yayımladığı listelerden derlendi (her oranın
  kaynağı dosyada yazılı). Kaynaklar yer yer çeliştiği için tek sayı yerine aralık verilir. Kesin
  hesap için kendi oranınızı girin.
- **Yalnızca komisyon düşülür.** Kargo, sabit hizmet bedeli, stopaj, reklam ve iade maliyeti hesaba
  dahil değildir (n11'in oransal hizmet bedelleri dahildir).
- **Pazar analizi satış rakamı içermez.** Sayfalarda satış adedi yazmaz; yorum sayısı ilginin
  dolaylı göstergesidir. Analiz yalnızca verdiğiniz listedeki ürünleri kapsar.
- **Kaydedilmiş sayfa okuma deneyseldir.** HTML okuyucu, sayfanın içine gömülü ürün listesini
  arar ve yapay bir örnekle test edilmiştir; gerçek pazaryeri sayfalarında henüz doğrulanmadı.
  Çalışmazsa CSV yolunu kullanın.
- **Bir veri uydurulmaz.** Oran veya yorum bilgisi yoksa "veri yok" yazar; aralıklar çakışıyorsa
  kesin sıralama yapılamadığını söyler.

## Veri ve gizlilik

Bu araç hiçbir siteye bağlanmaz ve hiçbir yere veri göndermez. Hesap, kendi bilgisayarınızda,
sizin verdiğiniz dosya ve rakamlarla yapılır.

## Sorumluluk notu

Bu araç Trendyol, Hepsiburada, n11 veya Amazon ile bağlantılı değildir ve onlar tarafından
onaylanmamıştır. Sonuçlar bilgi amaçlıdır; fiyatlama veya yatırım kararı vermeden önce kendi satıcı
panelinizdeki güncel oranları kontrol edin. Yazılım MIT lisansıyla, garanti verilmeden sunulur.

## Geliştirme

```bash
python -m unittest        # 36 test
```

Komisyon oranlarını güncellemek için `veri/komisyon.json` dosyasını düzenleyin; `es_anlamlilar`
listesi, kullanıcının yazdığı kelimeleri kategoriye bağlar.
