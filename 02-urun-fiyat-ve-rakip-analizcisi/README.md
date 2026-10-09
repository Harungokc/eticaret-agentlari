# Ürün, Fiyat ve Rakip Analizcisi

Bir ürünü satmadan ya da fiyatını değiştirmeden önce üç soruya yanıt verir:

| Soru | Araç ne gösterir |
|---|---|
| **Bu ürünün pazardaki ortalaması ne?** | Ortalama ve ortanca fiyat, en düşük–en yüksek, ortalama puan, yorum ve favori sayıları, ücretsiz kargo oranı |
| **Fiyatım pazarda nerede duruyor?** | Kaç ürün sizden ucuz, kaçı pahalı; ortancadan farkınız; ürünlerin yoğunlaştığı fiyat aralığı; en çok ilgi gören fiyat dilimi |
| **Rakiplerime göre neredeyim?** | Fiyat, puan, yorum, favori ve kargoda sıranız; öne geçtiğiniz ve geride kaldığınız noktalar |

Sonucu sohbette özetler ve üzerinde oynayabileceğiniz bir **Excel dosyası** olarak verir. Ücretsiz,
açık kaynak (MIT). Kod bilmeniz gerekmez.

## Claude ya da ChatGPT sohbetinde kullanın

Serideki bütün araçları tek seferde yüklemek için [tek paketi](../README.md) kullanabilirsiniz. Yalnızca bu aracı isterseniz:

**1. Paketi indirin:** [urun-fiyat-rakip-analizcisi.zip](https://github.com/Harungokc/eticaret-agentlari/releases/latest/download/urun-fiyat-rakip-analizcisi.zip) (ZIP'ten çıkarmayın)

**2. Asistanınıza yükleyin:**

| | Nasıl yüklenir |
|---|---|
| **Claude** (claude.ai ya da uygulama) | **Customize → Skills → + → Upload a skill** deyip ZIP dosyasını seçin. Bir kez eklenir, her sohbette hazırdır. *Settings → Capabilities* altında kod yürütme açık olmalıdır. |
| **ChatGPT** | Yeni sohbette ZIP dosyasını ekleyin ve şunu yazın: *"Bu ZIP dosyasını aç, içindeki SKILL.md dosyasını oku ve oradaki talimatlara göre çalış."* |

**3. Ürün listenizi verin ve sorun.** Örneğin:

> Aşağıda Trendyol'da "çelik termos 500 ml" aramasında gördüğüm ürünler var. Benim ürünüm 389,90 TL,
> puanı 4,3, 86 yorumu var. Pazarın ortalamasını çıkar, fiyatımın yerini göster ve rakiplerime göre
> nerede geride kaldığımı söyle.
>
> *(ürünleri ad, marka, fiyat, puan, yorum olarak alt alta yazın ya da bir dosya yükleyin)*

## Ürün listesini nasıl hazırlarım

Araç pazaryerlerinden **veri çekmez**; listeyi siz verirsiniz. Üç yol var:

- Pazaryerinde aramayı yapıp gördüğünüz ürünleri sohbete elle yazın.
- Arama sayfasındaki ürünleri seçip kopyalayın ve sohbete yapıştırın; asistan ürünleri ayıklar.
- [`ornek/sablon.csv`](ornek/sablon.csv) dosyasını Excel'de doldurup yükleyin.

Yalnızca **fiyat** zorunludur; puan, yorum, favori ve kargo bilgisi verdikçe analiz zenginleşir.
Ortalama ve konum için en az 5, tercihen 20 ve üzeri ürün; rakip karşılaştırması için 3–5 rakip
yeterlidir. Listeyi aynı tür ürünlerden oluşturun (örneğin yalnızca 500 ml termoslar).

## Örnek sonuç

Uydurma bir "çelik termos" listesiyle (30 ürün), 389,90 TL'lik bir ürün için:

```
ÜRÜN ORTALAMALARI — 30 ürün
  Ortalama fiyat                     420,53 TL
  Ortanca fiyat                      371,20 TL
  En düşük – en yüksek fiyat         199,00 TL – 849,90 TL
  Ürünlerin ortadaki yarısı          313,92 TL – 506,42 TL
  Yorum ağırlıklı ortalama fiyat     373,95 TL
  Puan                               ortalama 4,2, ortanca 4,3 (30 ürün)
  Yorum sayısı                       ortalama 393, ortanca 216 (30 ürün)
  Favori sayısı                      ortalama 1.724, ortanca 930 (30 ürün)
  Ücretsiz kargolu ürün oranı        %67 (30 ürün)

FİYAT KONUMU — 389,90 TL
  Karşılaştırılan ürün               30
  Sizden ucuz / aynı / pahalı        16 / 0 / 14
  Pazardaki yeriniz                  ortancanın üstünde (0–100 ölçeğinde 53; 0 en ucuz)
  Pazarın ortanca fiyatı             371,20 TL (ortancadan %5,0 pahalı)
  Ana fiyat aralığı                  313,92 TL – 506,42 TL (içindesiniz)
  Benzer fiyatlı ürünler (±%10)      5 ürün; ortanca puan 4,2, ortanca yorum 234
  Fiyat dilimleri (ürünler dört eşit gruba bölünür):
    1. 199,00 TL – 299,90 TL: 7 ürün, ortanca yorum 222
    2. 308,90 TL – 358,90 TL: 8 ürün, ortanca yorum 396  ← en çok ilgi gören
    3. 383,50 TL – 499,00 TL: 7 ürün, ortanca yorum 85
    4. 508,90 TL – 849,90 TL: 8 ürün, ortanca yorum 179

RAKİP KARŞILAŞTIRMASI — Paslanmaz Çelik Termos 500 ml (30 rakip)
  Fiyat                              siz: 389,90 TL | rakip ortancası: 371,20 TL | geride
                                     31 ürün içinde 17. sırada; rakip ortancasından 18,70 TL pahalı.
  Puan                               siz: 4,3 | rakip ortancası: 4,3 | aynı
                                     31 ürün içinde 13. sırada; rakip ortancasıyla aynı.
  Yorum sayısı                       siz: 86 | rakip ortancası: 216 | geride
                                     31 ürün içinde 24. sırada; rakip ortancasının 130 altında.
  Favori sayısı                      siz: 410 | rakip ortancası: 930 | geride
                                     31 ürün içinde 23. sırada; rakip ortancasının 520 altında.
  Kargo                              siz: ücretli | rakipler: 30 rakibin 20 tanesinde ücretsiz | geride
  Öne geçtiğiniz noktalar            yok
  Geride kaldığınız noktalar         Fiyat, Yorum sayısı, Favori sayısı, Kargo
```

## Kendi bilgisayarınızda çalıştırmak

Python 3.10 veya üstü yeterlidir; ek paket gerekmez.

```bash
python3 agent.py hepsi ornek/ornek_urunler.csv --excel sonuc.xlsx
python3 agent.py ortalama liste.csv
python3 agent.py konum liste.csv 349,90
python3 agent.py rakip liste.csv
python3 -m unittest          # testler
```

| Dosya | İşi |
|---|---|
| `analiz.py` | Ortalamalar, fiyat konumu, rakip karşılaştırması |
| `okuyucu.py` | CSV okuma |
| `rapor.py`, `xlsx.py` | Excel dosyası |
| `agent.py` | Komut satırı |
| `SKILL.md` | Yapay zekâ asistanı için talimatlar |

## Bilmeniz gereken sınırlar

- Sonuçlar verdiğiniz listeyle sınırlıdır; liste pazarın tamamını temsil etmeyebilir.
- Satış adedi ve ciro bilgisi yoktur. Yorum ve favori sayısı ilginin dolaylı göstergesidir.
- Araç fiyat önermez; pazarın nerede yoğunlaştığını gösterir. Fiyat kararı maliyetinize ve kâr
  hedefinize de bağlıdır. Komisyon ve kâr için: [Pazar ve Komisyon Analizcisi](../01-pazar-ve-komisyon-analizcisi/).
- Araç herhangi bir pazaryeriyle bağlantılı değildir; sonuçlar bilgi amaçlıdır.

**Geliştiren:** Harun Gökce — harungokce70@gmail.com · 0506 155 46 42
