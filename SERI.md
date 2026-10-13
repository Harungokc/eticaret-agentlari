# E-ticaret Analiz Agent'ları — Seri Planı

Dokuz agent'lık seri ve seriye sonradan eklenen araçlar. Her biri kendi klasöründe, tek başına çalışır. 1 ve 2 tek araçta, 3, 4 ve 5 tek araçta birleştirildi.

| # | Agent | Girdi | Çıktı | Durum |
|---|---|---|---|---|
| 1 | Komisyon Tarife Analizcisi | Kategori + satış fiyatı | Trendyol, Hepsiburada, n11 ve Amazon'da komisyon, ele geçen tutar, hangisi daha kârlı | Yayımlandı: `01-pazar-ve-komisyon-analizcisi/` |
| 2 | Pazar Analizi Agent'ı | Kategori veya ürün türü | Satıcı sayısı, öne çıkan markalar, fiyat bantları, rekabet yoğunluğu | Yayımlandı; 1 ile aynı araçta |
| 3 | Ürün Ortalama Analizcisi | Ürün adı | Ortalama, en düşük ve en yüksek fiyat; ortalama puan, yorum, sepet ve favori sayıları | Yayımlandı: `02-urun-fiyat-ve-rakip-analizcisi/` |
| 4 | Fiyat Konumlandırma Agent'ı | Ürün + fiyat | Pazardaki fiyat sıralaması, önerilen fiyat aralığı | Yayımlandı: `02-urun-fiyat-ve-rakip-analizcisi/` |
| 5 | Rakip Karşılaştırma Agent'ı | Ürün + 3–5 rakip ürün | Fiyat, puan, yorum, görsel, kargo ve kampanya tablosu; geride kalınan noktalar | Yayımlandı: `02-urun-fiyat-ve-rakip-analizcisi/` |
| 6 | Anahtar Kelime ve Başlık Analizcisi | Ürün adı | Rakip başlıklarındaki kelimeler, eksikler, önerilen başlık | Bekliyor |
| 7 | Trend ve Sezon Analizcisi | Kategori | Talebin arttığı aylar, yükselen ürün türleri, kampanya takvimi | Bekliyor |
| 8 | Kârlılık Simülatörü | Maliyet, fiyat, kategori, desi | Senaryolara göre ürün başına net kâr, zarar çizgisi | Bekliyor |
| 9 | Yeni Ürün Fırsat Agent'ı | İlgilenilen alan | Talebi yüksek, satıcısı az ürün türleri; ortalama fiyat ve rekabet düzeyi | Bekliyor |
| + | Satış Bölge Analizcisi | Sipariş listesi (il, ilçe, mahalle, tutar) | İl, bölge, ilçe ve mahalle bazında sipariş, ciro, ortalama sepet, iade oranı; sayılara dayanan bulgular ve öneriler; rapor sayfası ve Excel | Yayımlandı: `04-satis-bolge-analizcisi/` |
| + | Ürün Araştırma Agent'ı | İlgilenilen alan; kâr için Türkiye'deki ilan sayısı, maliyet ve satış fiyatı | Yurt dışında çok satan ve yeni yükselen ürünlerin kaynaklı raporu: satış gücü ve yükseliş puanı, ürün türü başına Çin'de fabrika liste fiyatı ve tedarik aramaları, risk uyarısı; Türkiye'de rekabet, ürün başına kâr ve karar | Yayımlandı: `05-urun-arastirma-agenti/` |

## Veri notu

- 1 ve 8 komisyon tablolarıyla ve satıcının girdiği rakamlarla çalışır.
- Diğer yedisi pazaryerindeki ürün verisine ihtiyaç duyar. Araçlar pazaryerlerinden veri çekmez;
  ürün verisini satıcı sağlar (liste yapıştırma ya da dosya yükleme).
- Ürün Araştırma Agent'ında aday ürünleri asistan internet aramasıyla toplar ve her rakamın kaynak
  bağlantısını yazar; hesabı yine araç yapar. Araç kendisi internete bağlanmaz.
