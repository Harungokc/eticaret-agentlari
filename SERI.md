# E-ticaret Analiz Agent'ları — Seri Planı

On agent'lık seri. Her biri kendi klasöründe, tek başına çalışır. 1 ve 2 tek araçta birleştirildi.

| # | Agent | Girdi | Çıktı | Durum |
|---|---|---|---|---|
| 1 | Komisyon Tarife Analizcisi | Kategori + satış fiyatı | Trendyol, Hepsiburada, n11 ve Amazon'da komisyon, ele geçen tutar, hangisi daha kârlı | İlk sürüm yazıldı; 2 ile birlikte `01-pazar-ve-komisyon-analizcisi/` içinde |
| 2 | Pazar Analizi Agent'ı | Kategori veya ürün türü | Satıcı sayısı, öne çıkan markalar, fiyat bantları, rekabet yoğunluğu | İlk sürüm yazıldı; 1 ile birlikte yayımlanıyor. Kaydedilmiş sayfa okuyucusu gerçek sayfada doğrulanacak |
| 3 | Ürün Ortalama Analizcisi | Ürün adı | Ortalama, en düşük ve en yüksek fiyat; ortalama puan, yorum, sepet ve favori sayıları | Bekliyor |
| 4 | Fiyat Konumlandırma Agent'ı | Ürün + fiyat | Pazardaki fiyat sıralaması, önerilen fiyat aralığı | Bekliyor |
| 5 | Rakip Karşılaştırma Agent'ı | Ürün + 3–5 rakip ürün | Fiyat, puan, yorum, görsel, kargo ve kampanya tablosu; geride kalınan noktalar | Bekliyor |
| 6 | Yorum Analiz Agent'ı | Bir ürün | Övülen ve şikâyet edilen konular, eklenmesi istenen özellikler | Bekliyor |
| 7 | Anahtar Kelime ve Başlık Analizcisi | Ürün adı | Rakip başlıklarındaki kelimeler, eksikler, önerilen başlık | Bekliyor |
| 8 | Trend ve Sezon Analizcisi | Kategori | Talebin arttığı aylar, yükselen ürün türleri, kampanya takvimi | Bekliyor |
| 9 | Kârlılık Simülatörü | Maliyet, fiyat, kategori, desi | Senaryolara göre ürün başına net kâr, zarar çizgisi | Bekliyor |
| 10 | Yeni Ürün Fırsat Agent'ı | İlgilenilen alan | Talebi yüksek, satıcısı az ürün türleri; ortalama fiyat ve rekabet düzeyi | Bekliyor |

## Veri notu

- 1 ve 9 komisyon tablolarıyla ve satıcının girdiği rakamlarla çalışır.
- Diğer sekizi pazaryerindeki ürün verisine ihtiyaç duyar. Trendyol ürün sayfalarına otomatik
  erişimi engelliyor; veri yolu (tarayıcı eklentisi, veri servisi veya satıcının yapıştırması)
  her agent için ayrıca kararlaştırılacak.
