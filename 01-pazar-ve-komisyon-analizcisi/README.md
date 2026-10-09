# Pazar ve Komisyon Analizcisi

Ürününüzü satmadan önce iki şeyi bilmek istersiniz: **pazar nasıl görünüyor** ve **hangi
pazaryerinde elinize ne kalacak**. Bu araç ikisini birlikte hesaplar ve sonucu hem ekranda hem de
üzerinde oynayabileceğiniz bir **Excel dosyası** olarak verir.

| | |
|---|---|
| **Kimin için** | Trendyol, Hepsiburada, n11 veya Amazon'da satış yapan ya da yapmayı düşünen herkes |
| **Ne gerekir** | Bir bilgisayar ve ücretsiz Python programı; kod bilgisi gerekmez |
| **Ücreti** | Yok. Açık kaynak, MIT lisanslı |
| **Verileriniz** | Bilgisayarınızdan çıkmaz; araç internete bağlanmaz |

---

## Başlatma

İlk kez kuruyorsanız adım adım anlatım [ayrıntılı kılavuzdadır](AYRINTILI-KILAVUZ.md#kurulum). Kurulum bittiyse bu
klasördeki dosyaya çift tıklamanız yeterli:

| Bilgisayarınız | Çift tıklayacağınız dosya |
|---|---|
| Windows | `Baslat.bat` |
| Mac | `Baslat.command` |

Siyah bir pencere açılır, ardından tarayıcınızda aracın sayfası belirir. İşiniz bitince siyah
pencereyi kapatın.

---

## Araç ne yapar

### Komisyon karşılaştırması

**Siz girersiniz:** kategori, satış fiyatı ve isterseniz ürün maliyeti.
**Araç gösterir:** dört pazaryerinin keseceği komisyon, elinize geçecek tutar ve kârınız.

Örnek — 899 TL'lik kadın ayakkabısı, maliyeti 400 TL:

| Pazaryeri | Komisyon oranı | Kesilen komisyon | Elinize geçen | Kârınız |
|---|---|---|---|---|
| Hepsiburada | %18 – %19,49 | 161,82 – 175,22 TL | 723,78 – 737,18 TL | 323,78 – 337,18 TL |
| n11 | %15 – %20,34 | 134,85 – 182,86 TL | 698,16 – 746,17 TL | 298,16 – 346,17 TL |
| Trendyol | %21,5 – %22,5 | 193,28 – 202,28 TL | 696,72 – 705,72 TL | 296,72 – 305,72 TL |

Bu tablodan şunu okursunuz: aynı ayakkabıdan Trendyol yaklaşık 200 TL, Hepsiburada yaklaşık 170 TL
kesiyor; Hepsiburada'da ürün başına 20–30 TL daha fazla kalıyor.

Sözleşmenizdeki gerçek oranı biliyorsanız **Kendi komisyon oranlarım** bölümüne yazın; aralık tek
sayıya iner ve sonuç kesinleşir.

### Pazar analizi

**Siz yüklersiniz:** bir ürün listesi (örneğin "erkek parfüm" aramasında gördüğünüz ürünler).
**Araç gösterir:**

| Bölüm | Size ne söyler |
|---|---|
| Fiyatlar | En düşük, en yüksek ve ortanca fiyat; ürünlerin yoğunlaştığı aralık |
| Fiyat bantları | Hangi fiyat aralığında kaç ürün var, hangisi daha çok ilgi görüyor |
| Öne çıkan markalar | Ürünlerin yüzde kaçı hangi markaya ait |
| İlgi ve rekabet | İlgi birkaç üründe mi toplanmış, yoksa dağınık mı |
| Okuma | Az rakipli ama ilgi gören bir fiyat bandı varsa onu gösterir |

Kategori de seçerseniz, pazarın ortanca fiyatı üzerinden komisyon karşılaştırması aynı sonuca
eklenir. Böylece "bu pazarda tipik fiyat şu, o fiyattan satarsam elime şu kalır" sorusunu tek adımda
cevaplarsınız.

### Excel çıktısı

Her sonucun üstünde **Excel olarak indir** düğmesi vardır. İnen dosya yalnızca bir döküm değil,
üzerinde çalışabileceğiniz bir şablondur:

- **Sarı hücreleri değiştirebilirsiniz:** satış fiyatı, maliyet ve komisyon oranları. Değiştirdiğiniz
  anda komisyon, elinize geçen tutar ve kâr Excel'in içinde yeniden hesaplanır.
- **"Fiyatı 50 TL artırsam ne olur?"** sorusunu aracı yeniden çalıştırmadan, doğrudan Excel'de
  deneyebilirsiniz.
- Pazar analizinde dosya üç sayfadır:

  | Sayfa | İçeriği |
  |---|---|
  | **Pazar** | Fiyat özeti, fiyat bantları, markalar, rekabet göstergeleri |
  | **Komisyon** | Pazarın ortanca fiyatına bağlı komisyon karşılaştırması |
  | **Ürünler** | Yüklediğiniz liste; buradaki fiyatları değiştirirseniz Pazar sayfası güncellenir |

---

## Ürün listesi nasıl hazırlanır

Pazar analizi bir liste ister. En kolay yol Excel'dir:

1. Bu klasördeki `ornek/sablon.csv` dosyasını Excel ile açın.
2. İncelemek istediğiniz aramayı pazaryerinde yapın ve gördüğünüz ürünleri satır satır yazın.

   | Sütun | Ne yazılır | Zorunlu mu |
   |---|---|---|
   | `ad` | Ürünün adı | Hayır |
   | `marka` | Markası | Hayır |
   | `fiyat` | Satış fiyatı | **Evet** |
   | `puan` | Yıldız puanı (ör. 4,5) | Hayır |
   | `yorum` | Yorum veya değerlendirme sayısı | Hayır |

3. Şablondaki iki örnek satırı silin.
4. **Dosya → Farklı Kaydet** deyip tür olarak **CSV UTF-8 (Virgülle ayrılmış)** seçin.
5. Araçta **Pazar analizi** sekmesinde dosyanızı seçip **Analiz et** düğmesine basın.

En az 8 ürün gerekir; 20–40 ürün daha güvenilir sonuç verir. Önce denemek isterseniz hazır
`ornek/ornek_urunler.csv` dosyasını yükleyin; bu dosya uydurma bir listedir, gerçek marka ya da fiyat
içermez.

---

## Sonuçları okurken

- **Oranlar yaklaşıktır.** Pazaryerleri komisyonlarını açık tek bir tabloda yayımlamıyor. Değerler
  açık kaynaklardan 8 Ekim 2026'da derlendi; her oranın kaynağı [`veri/komisyon.json`](veri/komisyon.json)
  dosyasında yazılıdır. Bağlayıcı oran satıcı panelinizdeki sözleşme ekranındadır.
- **Yalnızca komisyon düşülür.** Kargo, sabit hizmet bedeli, stopaj, reklam ve iade hesaba dahil
  değildir; gerçekte elinize geçen tutar daha düşük olur.
- **"Veri yok" bir hata değildir.** O kategori için o pazaryerinde oran bulunamadığını gösterir; araç
  tahmin yürütmez. Kendi oranınızı yazarak tamamlayabilirsiniz.
- **Pazar analizi satış rakamı içermez.** Yorum sayısı ilginin dolaylı göstergesidir; ciro tahmini
  yapılmaz ve analiz yüklediğiniz listeyle sınırlıdır.

Daha fazlası için ayrıntılı kılavuzdaki [Sonuçları nasıl okurum](AYRINTILI-KILAVUZ.md#sonuçları-nasıl-okurum) ve
[Sık sorulan sorular](AYRINTILI-KILAVUZ.md#sık-sorulan-sorular) bölümlerine bakın.

---

## Bu klasördeki dosyalar

| Dosya | İşi |
|---|---|
| `Baslat.bat`, `Baslat.command` | Çift tıklayarak başlatma |
| `ornek/sablon.csv` | Kendi ürün listenizi yazacağınız boş şablon |
| `ornek/ornek_urunler.csv` | Denemeniz için uydurma örnek liste |
| `veri/komisyon.json` | Komisyon oranları ve her oranın kaynağı |
| `arayuz.py` | Tarayıcıda açılan form arayüzü |
| `agent.py` | Komut satırından kullanım |
| `komisyon.py`, `pazar.py` | Hesaplamalar |
| `okuyucu.py` | CSV, JSON ve kaydedilmiş sayfa okuma |
| `excel.py` | Excel dosyası üretimi |
| `test_*.py` | Otomatik testler |

<details>
<summary><b>Geliştiriciler için: komut satırı ve testler</b></summary>

```bash
python arayuz.py                                                         # tarayıcı arayüzü
python agent.py komisyon "kadın ayakkabı" 899 --maliyet 400 --excel sonuc.xlsx
python agent.py komisyon "telefon kılıfı" 249 --trendyol 26              # kendi oranınızla
python agent.py pazar ornek/ornek_urunler.csv --kategori "erkek parfüm" --excel pazar.xlsx
python agent.py kategoriler
python -m unittest                                                       # 61 test
```

Tasarım ilkeleri:

- **Sayı uydurulmaz.** Oran ya da yorum bilgisi yoksa "veri yok" yazılır; aralıklar çakışıyorsa kesin
  sıralama yapılmaz.
- **Dışarıya bağlantı yok.** Arayüz yalnızca `127.0.0.1` adresini dinler ve başka sitelerden gelen
  istekleri reddeder. Yüklenen dosyadaki metin ne sayfada ne de Excel'de çalıştırılabilir içerik
  olarak yer alır.
- **Bağımlılık yok.** Excel dosyası dahil her şey Python standart kütüphanesiyle üretilir.

Komisyon oranlarını güncellemek için `veri/komisyon.json` dosyasını düzenleyin; `es_anlamlilar`
listesi komut satırında yazılan kelimeleri kategoriye bağlar. Veri bütünlüğü testleri kaynaksız ya da
geçersiz oranı yakalar.

</details>
