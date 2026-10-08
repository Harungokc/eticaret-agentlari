# Pazar ve Komisyon Analizcisi

Kurulum ve kullanım kılavuzu [ana sayfadadır](../README.md).

**Hızlı başlangıç:** Bu klasördeki `Baslat.bat` (Windows) ya da `Baslat.command` (Mac) dosyasına çift
tıklayın; araç tarayıcınızda açılır.

## Bu klasörde neler var

| Dosya | İşi |
|---|---|
| `Baslat.bat`, `Baslat.command` | Çift tıklayarak başlatma dosyaları |
| `arayuz.py` | Tarayıcıda açılan form arayüzü |
| `agent.py` | Komut satırından kullanım |
| `komisyon.py` | Kategori eşleştirme ve komisyon hesabı |
| `pazar.py` | Ürün listesinden pazar analizi |
| `okuyucu.py` | CSV, JSON ve kaydedilmiş sayfa okuma |
| `veri/komisyon.json` | Komisyon oranları ve her oranın kaynağı |
| `ornek/sablon.csv` | Kendi ürün listenizi yazmanız için boş şablon |
| `ornek/ornek_urunler.csv` | Denemeniz için uydurma örnek liste |
| `test_*.py` | Testler (`python -m unittest`) |

## Komut satırı

```bash
python agent.py komisyon "kadın ayakkabı" 899
python agent.py komisyon "telefon kılıfı" 249 --maliyet 80 --trendyol 26
python agent.py pazar ornek/ornek_urunler.csv --kategori "erkek parfüm" --maliyet 150
python agent.py kategoriler
```

## Komisyon oranlarını güncellemek

`veri/komisyon.json` düz bir JSON dosyasıdır. Her kategoride pazaryeri başına en düşük ve en yüksek
oran ile kaynağı yazılıdır; `es_anlamlilar` listesi komut satırında yazılan kelimeleri kategoriye
bağlar. Değişiklikten sonra `python -m unittest` çalıştırın; veri bütünlüğü testleri kaynaksız ya da
geçersiz oranı yakalar.

## Tasarım ilkeleri

- **Sayı uydurulmaz.** Oran ya da yorum bilgisi yoksa "veri yok" yazılır; aralıklar çakışıyorsa kesin
  sıralama yapılmaz.
- **Dışarıya bağlantı yok.** Arayüz yalnızca `127.0.0.1` adresini dinler; başka sitelerden gelen
  istekleri reddeder ve yüklenen dosyadaki metni sayfada çalıştırılabilir içerik olarak göstermez.
- **Bağımlılık yok.** Yalnızca Python standart kütüphanesi kullanılır.
