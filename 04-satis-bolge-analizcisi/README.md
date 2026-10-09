# Satış Bölge Analizcisi

Satışlarınız nereye gidiyor? Bu araç sipariş listenizdeki il ve ilçe bilgisini sayar:

| Soru | Araç ne gösterir |
|---|---|
| **En çok nereye satıyorum?** | İl, bölge ve ilçe bazında sipariş sayısı, pay, ciro ve ortalama sepet |
| **Satışlarım ne kadar yoğunlaşmış?** | İlk 3 ve ilk 10 ilin payı; sipariş gelmeyen iller |
| **Nerede sorun var?** | İl ve bölge bazında iade oranı; her ilde en çok satan ürün |

Reklamı hangi illere vereceğinize, hangi bölge için kargo anlaşması yapacağınıza karar verirken
kullanabilirsiniz. Sonucu **Excel dosyası** olarak verir. Ücretsiz, açık kaynak (MIT).

## Önce: müşteri bilgilerini çıkarın

Sipariş dökümleri müşteri adı, telefon ve açık adres içerir. **Bu analiz için bunların hiçbiri
gerekmez.** Dosyayı Claude ya da ChatGPT'ye yüklemeden önce Excel'de bu sütunları silin; yalnızca
şunlar kalsın: il, ilçe, tutar, ürün, sipariş no, durum.

Müşterilerinizin kişisel verilerini bir yapay zekâ hizmetine yüklemek, KVKK kapsamında sizin
sorumluluğunuzdadır. Araç bu sütunları dosyada olsa bile okumaz ve çıktıya yazmaz, ama dosyayı
yüklediğiniz anda o hizmete göndermiş olursunuz; bu yüzden silme işini yüklemeden önce yapın.

## Claude ya da ChatGPT sohbetinde kullanın

Tek tek yüklemek yerine serideki bütün araçları içeren [tek paketi](../README.md) kullanabilirsiniz.
Yalnızca bu aracı isterseniz: [satis-bolge-analizcisi.zip](https://github.com/Harungokc/eticaret-agentlari/releases/latest/download/satis-bolge-analizcisi.zip)

Sipariş dökümünüzü (kişisel sütunları sildikten sonra) yükleyin ve sorun:

> Bu sipariş listesinden satışlarımın il ve bölge dağılımını çıkar. En güçlü olduğum iller hangileri,
> nerelere hiç satamıyorum, iade oranı nerede yüksek?

## Örnek sonuç

Uydurma 400 siparişle:

```
SATIŞ BÖLGE ANALİZİ — 393 sipariş, 26 il, ciro 177.430,70 TL
  Siparişlerde ilk 3 ilin payı %57,8, ilk 10 ilin payı %81,7.
  İptal edilen 7 satır analize girmedi.

BÖLGELER
  Marmara                 160 sipariş   %40,7   ciro     72.879,90 TL   ort. sepet    455,50 TL   iade   %5,6
  İç Anadolu               93 sipariş   %23,7   ciro     43.408,40 TL   ort. sepet    466,76 TL   iade   %1,1
  Ege                      63 sipariş   %16,0   ciro     26.832,10 TL   ort. sepet    425,91 TL   iade   %4,8
  Akdeniz                  45 sipariş   %11,5   ciro     18.354,60 TL   ort. sepet    407,88 TL   iade   %6,7
  Karadeniz                16 sipariş    %4,1   ciro      7.707,90 TL   ort. sepet    481,74 TL   iade   %6,2
  Güneydoğu Anadolu        13 sipariş    %3,3   ciro      5.628,40 TL   ort. sepet    432,95 TL   iade  %15,4
  Doğu Anadolu              3 sipariş    %0,8   ciro      2.619,40 TL   ort. sepet    873,13 TL   iade   %0,0

EN ÇOK SİPARİŞ GELEN İLLER
  İstanbul                118 sipariş   %30,0   ciro     54.875,10 TL   ort. sepet    465,04 TL   iade   %5,1
  Ankara                   65 sipariş   %16,5   ciro     32.041,60 TL   ort. sepet    492,95 TL   iade   %0,0
  İzmir                    44 sipariş   %11,2   ciro     19.284,30 TL   ort. sepet    438,28 TL   iade   %6,8
  Antalya                  21 sipariş    %5,3   ciro      7.077,70 TL   ort. sepet    337,03 TL   iade   %9,5
  Bursa                    19 sipariş    %4,8   ciro      7.847,80 TL   ort. sepet    413,04 TL   iade  %10,5
  Adana                    13 sipariş    %3,3   ciro      4.928,50 TL   ort. sepet    379,12 TL   iade   %7,7
  Kocaeli                  12 sipariş    %3,1   ciro      5.638,40 TL   ort. sepet    469,87 TL   iade   %8,3
```

## Kendi bilgisayarınızda çalıştırmak

Python 3.10 veya üstü yeterlidir; ek paket gerekmez. Bu yolda dosyanız bilgisayarınızdan çıkmaz.

```bash
python3 agent.py analiz ornek/ornek_siparisler.csv
python3 agent.py analiz siparisler.csv --excel sonuc.xlsx
python3 -m unittest          # testler
```

Dosya, ilk satırında başlıklar olan bir CSV'dir ([şablon](ornek/sablon.csv)). Zorunlu sütun yalnızca
`il`dir; `ilçe`, `tutar`, `ürün`, `sipariş no` ve `durum` isteğe bağlıdır. İl adlarının yazımı
önemli değildir (İSTANBUL, istanbul, Urfa, K.Maraş tanınır).

## Bilmeniz gereken sınırlar

- Sonuçlar verdiğiniz listeyle sınırlıdır; tek bir ayın siparişleri mevsim etkisi taşıyabilir.
- Bir ilin payının yüksek olması nüfusla da ilgilidir; araç nüfus verisi içermez.
- İade oranı az siparişli illerde yanıltıcı olabilir.
- Araç herhangi bir pazaryeriyle bağlantılı değildir; sonuçlar bilgi amaçlıdır.

**Geliştiren:** Harun Gökce — harungokce70@gmail.com · 0506 155 46 42
