# Pazar ve Komisyon Analizcisi

**E-ticaret satıcıları için ücretsiz, açık kaynak analiz aracı.** Ürününüzü hangi pazaryerinde
satarsanız elinize ne kalacağını ve girdiğiniz pazarın nasıl göründüğünü gösterir.

[![Testler](https://github.com/Harungokc/eticaret-agentlari/actions/workflows/test.yml/badge.svg)](https://github.com/Harungokc/eticaret-agentlari/actions/workflows/test.yml)
[![Lisans: MIT](https://img.shields.io/badge/lisans-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)

Kod yazmayı bilmeniz gerekmez. Kurulum bir kez yapılır, yaklaşık 5 dakika sürer; sonrasında bir
dosyaya çift tıklarsınız ve araç tarayıcınızda bir sayfa olarak açılır.

> **Gizlilik:** Araç kendi bilgisayarınızda çalışır. Girdiğiniz fiyat, maliyet ve yüklediğiniz dosya
> internete gönderilmez; hiçbir pazaryerine bağlanılmaz.

---

## İçindekiler

- [Ne işe yarar](#ne-işe-yarar)
- [Kurulum](#kurulum)
- [Nasıl kullanılır](#nasıl-kullanılır)
- [Sonuçları nasıl okurum](#sonuçları-nasıl-okurum)
- [Sık sorulan sorular](#sık-sorulan-sorular)
- [Bilmeniz gereken sınırlar](#bilmeniz-gereken-sınırlar)
- [Geliştiriciler için](#geliştiriciler-için)

---

## Ne işe yarar

### 1. Komisyon karşılaştırması

Kategorinizi ve satış fiyatınızı girersiniz; Trendyol, Hepsiburada, n11 ve Amazon Türkiye'nin
keseceği komisyonu ve elinize geçecek tutarı yan yana görürsünüz. Maliyetinizi de yazarsanız
kârınız hesaplanır.

Örnek: 899 TL'lik bir kadın ayakkabısı, maliyeti 400 TL.

| Pazaryeri | Komisyon oranı | Kesilen komisyon | Elinize geçen | Kârınız |
|---|---|---|---|---|
| Hepsiburada | %18 – %19,49 | 161,82 – 175,22 TL | 723,78 – 737,18 TL | 323,78 – 337,18 TL |
| n11 | %15 – %20,34 | 134,85 – 182,86 TL | 698,16 – 746,17 TL | 298,16 – 346,17 TL |
| Trendyol | %21,5 – %22,5 | 193,28 – 202,28 TL | 696,72 – 705,72 TL | 296,72 – 305,72 TL |

### 2. Pazar analizi

Bir ürün listesi yüklersiniz (örneğin "erkek parfüm" aramasında gördüğünüz ürünler); araç size o
pazarın fotoğrafını çıkarır:

- **Fiyatlar:** en düşük, en yüksek, ortanca fiyat ve ürünlerin yoğunlaştığı aralık
- **Fiyat bantları:** hangi fiyat aralığında kaç ürün var
- **Öne çıkan markalar:** ürünlerin yüzde kaçı hangi markaya ait
- **Rekabet durumu:** ilgi birkaç üründe mi toplanmış, yoksa dağınık mı
- **Boş bant:** az rakibi olan ama ilgi gören bir fiyat aralığı varsa onu gösterir

Kategori de seçerseniz, pazarın ortanca fiyatı üzerinden komisyon karşılaştırması aynı sayfaya
eklenir.

---

## Kurulum

Kurulum üç adımdır ve bir kez yapılır.

### Adım 1 — Python'u kurun

Araç, Python adlı ücretsiz programla çalışır.

<details>
<summary><b>Windows</b></summary>

1. [python.org/downloads](https://www.python.org/downloads/) adresine gidin ve sarı
   **Download Python** düğmesine basın.
2. İnen dosyayı açın.
3. Açılan pencerenin en altındaki **"Add python.exe to PATH"** kutusunu işaretleyin. Bu kutu
   işaretlenmezse araç Python'u bulamaz.
4. **Install Now** düğmesine basın ve kurulumun bitmesini bekleyin.

</details>

<details>
<summary><b>Mac</b></summary>

1. [python.org/downloads](https://www.python.org/downloads/) adresine gidin ve sarı
   **Download Python** düğmesine basın.
2. İnen `.pkg` dosyasını açın ve **Sürdür** diyerek kurulumu tamamlayın.

</details>

### Adım 2 — Aracı indirin

1. **[Buraya tıklayarak aracı indirin (ZIP)](https://github.com/Harungokc/eticaret-agentlari/archive/refs/heads/main.zip)**
2. İnen `eticaret-agentlari-main.zip` dosyasına çift tıklayarak açın (Windows'ta: sağ tık →
   **Tümünü ayıkla**).
3. Çıkan `eticaret-agentlari-main` klasörünü kolay bulacağınız bir yere, örneğin Masaüstü'ne
   taşıyın.

### Adım 3 — Başlatın

`eticaret-agentlari-main` klasörünü, içindeki `01-pazar-ve-komisyon-analizcisi` klasörünü açın ve
başlatma dosyasına çift tıklayın:

| Bilgisayarınız | Çift tıklayacağınız dosya |
|---|---|
| Windows | `Baslat.bat` |
| Mac | `Baslat.command` |

Siyah bir pencere açılır ve birkaç saniye içinde tarayıcınızda **Pazar ve Komisyon Analizcisi**
sayfası belirir. Siyah pencere açık kaldığı sürece araç çalışır; işiniz bitince o pencereyi
kapatmanız yeterlidir.

<details>
<summary><b>Windows "Bilgisayarınızı koruduk" uyarısı verirse</b></summary>

Uyarıdaki **Ek bilgi** yazısına, ardından **Yine de çalıştır** düğmesine basın. Bu uyarı, internetten
indirilen her yeni dosyada çıkar.

</details>

<details>
<summary><b>Mac "açılamıyor" veya "geliştirici doğrulanamıyor" uyarısı verirse</b></summary>

`Baslat.command` dosyasına sağ tıklayın (ya da Control tuşuna basılı tutarak tıklayın), **Aç**'ı seçin
ve çıkan pencerede yeniden **Aç**'a basın.

Yeni macOS sürümlerinde bu seçenek çıkmazsa: **Sistem Ayarları → Gizlilik ve Güvenlik** bölümüne
girin, en altta `Baslat.command` için görünen **Yine de Aç** düğmesine basın.

Bu da olmazsa şu yolu izleyin:

1. **Terminal** uygulamasını açın (Spotlight'ta "Terminal" yazın).
2. `cd ` yazın (sonunda bir boşluk bırakın), `01-pazar-ve-komisyon-analizcisi` klasörünü Terminal
   penceresine sürükleyip bırakın ve Enter'a basın.
3. `python3 arayuz.py` yazıp Enter'a basın.

</details>

---

## Nasıl kullanılır

### Komisyon karşılaştırması

1. **Komisyon karşılaştırması** sekmesinde kategorinizi listeden seçin.
2. **Satış fiyatı**nı yazın (`899`, `1.299,90` gibi).
3. İsterseniz **Ürün maliyeti**ni yazın; kârınız da hesaplanır.
4. **Hesapla** düğmesine basın.

Sözleşmenizdeki gerçek komisyon oranını biliyorsanız **Kendi komisyon oranlarım** bölümünü açıp
yazın. O zaman yaklaşık aralık yerine sizin oranınız kullanılır ve sonuç kesinleşir. Oranınızı
satıcı panelinizdeki sözleşme veya komisyon ekranında bulabilirsiniz.

### Pazar analizi

Bu bölüm bir ürün listesi ister. Listeyi Excel'de hazırlayabilirsiniz:

1. Klasördeki `ornek/sablon.csv` dosyasını Excel ile açın.
2. İncelemek istediğiniz pazaryerinde aramanızı yapın (örneğin "erkek parfüm") ve gördüğünüz
   ürünleri satır satır yazın. Sütunlar:

   | Sütun | Ne yazılır | Zorunlu mu |
   |---|---|---|
   | `ad` | Ürünün adı | Hayır |
   | `marka` | Markası | Hayır |
   | `fiyat` | Satış fiyatı | **Evet** |
   | `puan` | Yıldız puanı (ör. 4,5) | Hayır |
   | `yorum` | Yorum veya değerlendirme sayısı | Hayır |

3. Şablondaki iki örnek satırı silin.
4. **Dosya → Farklı Kaydet** deyip dosya türü olarak **CSV UTF-8 (Virgülle ayrılmış)** seçin.
5. Araçta **Pazar analizi** sekmesine geçin, dosyanızı seçin ve **Analiz et** düğmesine basın.

En az 8 ürün gerekir; 20–40 ürün daha güvenilir sonuç verir. Puan ve yorum sütunlarını
doldurursanız rekabet ve ilgi bölümleri de hesaplanır.

Önce nasıl göründüğünü denemek isterseniz hazır `ornek/ornek_urunler.csv` dosyasını yükleyin. Bu
dosya tamamen uydurma bir listedir; gerçek marka, ürün veya fiyat içermez.

> **Deneysel:** Arama sayfasını tarayıcınızdan "Farklı kaydet → Web sayfası, tamamı" ile kaydedip
> `.html` dosyası olarak da yükleyebilirsiniz. Bu yol her sayfada çalışmayabilir; çalışmazsa araç
> bunu söyler ve Excel yolunu kullanmanız gerekir.

---

## Sonuçları nasıl okurum

**Oranlar neden aralık olarak yazıyor (ör. %17 – %22,5)?**
Pazaryerleri komisyon oranlarını herkese açık tek bir tabloda yayımlamıyor ve oran alt kategoriye,
markaya, satıcı seviyesine göre değişiyor. Araç, açık kaynaklarda verilen en düşük ve en yüksek
değeri gösterir. Kendi oranınızı girerseniz aralık tek sayıya iner.

**"Oran aralıkları çakışıyor" ne demek?**
İki pazaryerinin aralıkları üst üste biniyorsa hangisinin daha kârlı olduğu sizin sözleşme oranınıza
bağlıdır. Araç bu durumda kesin bir kazanan söylemez; kendi oranlarınızı girmenizi ister.

**"Veri yok" ne demek?**
O kategori için o pazaryerinde bir oran bulunamadı demektir. Araç tahmin yürütmez. Kendi oranınızı
girerek o pazaryerini de karşılaştırmaya katabilirsiniz.

**"Ortanca fiyat" nedir?**
Ürünler fiyata göre sıralandığında tam ortada kalan fiyattır. Birkaç çok pahalı ürün ortalamayı
yukarı çeker; ortanca bundan etkilenmediği için pazarın tipik fiyatını daha iyi gösterir.

**"Pazar yoğunlaşmış / orta / dağınık" ne demek?**
En çok yorum alan 10 ürünün, listedeki toplam yorumların ne kadarını topladığına bakılır. %60 ve
üzeriyse ilgi birkaç üründe toplanmıştır (yoğunlaşmış); %35'in altındaysa ürünlere yayılmıştır
(dağınık). Bu kaba bir göstergedir, kesin bir ölçü değildir.

---

## Sık sorulan sorular

**Ücretli mi?**
Hayır. Araç ücretsizdir ve açık kaynaktır; dilediğiniz gibi kullanabilir, değiştirebilirsiniz.

**Verilerim bir yere gidiyor mu?**
Hayır. Araç internete bağlanmaz. Tarayıcıda açılan sayfa da kendi bilgisayarınızdan gelir; adres
çubuğunda `127.0.0.1` yazması bunu gösterir.

**Çift tıkladım, siyah pencere açılıp hemen kapandı.**
Python kurulu değildir ya da Windows'ta kurulum sırasında "Add python.exe to PATH" kutusu
işaretlenmemiştir. Python'u kaldırıp [Adım 1](#adım-1--pythonu-kurun)'deki gibi yeniden kurun.

**Tarayıcıda sayfa açılmadı.**
Siyah pencerede `http://127.0.0.1:8765/` gibi bir adres yazar. O adresi tarayıcınızın adres
çubuğuna kopyalayın.

**"Program yanıt vermedi" yazıyor.**
Siyah pencere kapanmıştır. Başlatma dosyasına yeniden çift tıklayın ve sayfayı yenileyin.

**Kategorim listede yok.**
Size en yakın kategoriyi seçip **Kendi komisyon oranlarım** bölümüne gerçek oranınızı yazın. Yeni
kategori önerinizi [buradan](https://github.com/Harungokc/eticaret-agentlari/issues) iletebilirsiniz.

**Excel dosyam (.xlsx) neden kabul edilmiyor?**
Araç şimdilik CSV okur. Excel'de **Farklı Kaydet → CSV UTF-8** seçeneğiyle kaydedin.

**Yapay zekâ kullanıyor mu?**
Hayır. Bütün sonuçlar düz hesapla üretilir; her sayı girdiğiniz veriden ve komisyon tablosundan
türetilir.

**Bir hata buldum ya da önerim var.**
[Buradan bildirin](https://github.com/Harungokc/eticaret-agentlari/issues); "New issue" düğmesine
basıp yazmanız yeterli.

---

## Bilmeniz gereken sınırlar

Araç ne yaptığı kadar ne yapmadığı konusunda da açık olmalı:

- **Komisyon oranları yaklaşıktır.** Değerler e-ticaret yazılım firmalarının yayımladığı listelerden
  8 Ekim 2026'da derlendi; her oranın kaynağı [`veri/komisyon.json`](01-pazar-ve-komisyon-analizcisi/veri/komisyon.json)
  dosyasında yazılıdır. Bağlayıcı oran, satıcı panelinizdeki sözleşme ekranındadır.
- **Yalnızca komisyon düşülür.** Kargo, sabit hizmet bedeli, stopaj, reklam ve iade maliyeti hesaba
  dahil değildir; gerçekte elinize geçen tutar tablodakinden düşük olur. (n11'in oransal hizmet
  bedelleri hesaba dahildir.)
- **Pazar analizi satış rakamı içermez.** Pazaryeri sayfalarında satış adedi yazmaz. Yorum sayısı
  ilginin dolaylı göstergesidir; ciro tahmini yapılmaz.
- **Analiz, yüklediğiniz listeyle sınırlıdır.** 30 ürün yazdıysanız 30 ürünlük bir pazar fotoğrafı
  alırsınız.
- **Bazı kategorilerde Amazon ve n11 verisi eksiktir.** Bu durumda "veri yok" yazar.

### Sorumluluk notu

Bu araç Trendyol, Hepsiburada, n11 veya Amazon ile bağlantılı değildir ve onlar tarafından
onaylanmamıştır. Sonuçlar bilgi amaçlıdır. Fiyatlama veya yatırım kararı vermeden önce satıcı
panelinizdeki güncel oranları kontrol edin. Yazılım [MIT lisansı](LICENSE) ile, garanti verilmeden
sunulur.

---

## Geliştiriciler için

Proje saf Python'dur; standart kütüphane dışında bağımlılığı yoktur.

```bash
git clone https://github.com/Harungokc/eticaret-agentlari.git
cd eticaret-agentlari/01-pazar-ve-komisyon-analizcisi

python arayuz.py                                              # tarayıcı arayüzü
python agent.py komisyon "kadın ayakkabı" 899 --maliyet 400   # komut satırı
python agent.py pazar ornek/ornek_urunler.csv --kategori "erkek parfüm"
python -m unittest                                            # testler
```

| Dosya | İşi |
|---|---|
| `komisyon.py` | Kategori eşleştirme ve komisyon hesabı |
| `pazar.py` | Ürün listesinden pazar analizi |
| `okuyucu.py` | CSV, JSON ve kaydedilmiş sayfa okuma |
| `arayuz.py` | Yalnızca `127.0.0.1` üzerinde çalışan tarayıcı arayüzü |
| `agent.py` | Komut satırı |
| `veri/komisyon.json` | Komisyon oranları ve kaynakları |

Testler her değişiklikte Windows, macOS ve Linux üzerinde otomatik çalışır. Katkılar ve oran
düzeltmeleri memnuniyetle karşılanır; oran değişikliklerinde kaynak belirtmeniz yeterlidir.

Bu araç, e-ticaret satıcıları için hazırlanan bir analiz araçları serisinin ilkidir. Planlanan
diğer araçlar için [SERI.md](SERI.md) dosyasına bakabilirsiniz.

## Lisans

[MIT](LICENSE) © 2026 Harun Gökçe
