# E-ticaret Analiz Araçları

**Trendyol, Hepsiburada, n11 ve Amazon satıcıları için ücretsiz, açık kaynak analiz araçları.**
Claude'a ya da ChatGPT'ye yüklersiniz, sonra konuşur gibi sorarsınız. Kod bilmeniz gerekmez.

[![Testler](https://github.com/Harungokc/eticaret-agentlari/actions/workflows/test.yml/badge.svg)](https://github.com/Harungokc/eticaret-agentlari/actions/workflows/test.yml)
[![Lisans: MIT](https://img.shields.io/badge/lisans-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)

## Ne sorabilirsiniz

| Sorunuz | Araç | Sizden gereken |
|---|---|---|
| Hangi pazaryerinde elime ne kalır? | [Pazar ve Komisyon Analizcisi](01-pazar-ve-komisyon-analizcisi/) | Kategori ve satış fiyatı |
| Ürünün pazar ortalaması ne? Fiyatım nerede duruyor? Rakiplerime göre nerede gerideyim? | [Ürün, Fiyat ve Rakip Analizcisi](02-urun-fiyat-ve-rakip-analizcisi/) | Ürün listesi |
| Müşteriler neden şikâyet ediyor, üründe ne istiyor? | [Yorum Analizcisi](03-yorum-analizcisi/) | Ürün yorumları |
| Satışlarım hangi illere gidiyor? Nerede güçlüyüm? | [Satış Bölge Analizcisi](04-satis-bolge-analizcisi/) | Sipariş listesi (il, ilçe, tutar) |

Her araç sonucu sohbette özetler ve üzerinde oynayabileceğiniz bir **Excel dosyası** verir.

## Kurulum: tek dosya, üç adım

**1. Paketi indirin:** [eticaret-analiz-araclari.zip](https://github.com/Harungokc/eticaret-agentlari/releases/latest/download/eticaret-analiz-araclari.zip) — dört aracın hepsi içinde. ZIP'ten çıkarmayın.

**2. Asistanınıza yükleyin:**

| | Nasıl yüklenir |
|---|---|
| **Claude** (claude.ai ya da uygulama) | **Customize → Skills → + → Upload a skill** deyip ZIP dosyasını seçin. Bir kez eklenir, her sohbette hazırdır. *Settings → Capabilities* altında kod yürütme açık olmalıdır. |
| **ChatGPT** | Yeni sohbette ZIP dosyasını ekleyin ve şunu yazın: *"Bu ZIP dosyasını aç, içindeki SKILL.md dosyasını oku ve oradaki talimatlara göre çalış."* Her yeni sohbette yeniden yüklenir. |

**3. Sorun.** Örnekler:

- *"899 liralık kadın ayakkabıyı hangi pazaryerinde satmalıyım? Maliyetim 400 lira."*
- *"Aşağıda 'çelik termos' aramasında gördüğüm ürünler var. Benim fiyatım 389,90 TL; pazardaki yerimi ve rakiplerime göre durumumu çıkar."*
- *"Bunlar ürünümün yorumları. Müşteriler en çok neden şikâyet ediyor, ne istiyorlar?"*
- *"Bu sipariş listesinden satışlarımın il ve bölge dağılımını çıkar."*

> **Denenme durumu:** Araçların kendisi Windows, macOS ve Linux'ta otomatik testlerden geçer. Paketin
> Claude ve ChatGPT sohbet ekranlarına yüklenmesi henüz her planda denenmemiştir; takıldığınız yeri
> [bildirirseniz](https://github.com/Harungokc/eticaret-agentlari/issues) düzeltiriz.

## Nasıl çalışır

- **Araçlar hesaplar, asistan anlatır.** Her tutar, oran ve sayı bu depodaki Python kodundan gelir;
  asistan rakam uydurmaz. Aynı girdiye her zaman aynı sonucu alırsınız.
- **Veri çekilmez.** Araçlar hiçbir pazaryerine bağlanmaz. Ürün listesini, yorumları ve siparişleri
  siz verirsiniz: yazarak, sayfadan kopyalayıp yapıştırarak ya da dosya yükleyerek.
- **Kurulum gerektirmez.** Paket ek program ve internet bağlantısı istemez; asistanınızın kod
  çalıştırma ortamında çalışır.

## Verileriniz

- Girdiğiniz bilgiler aracın yazarına gönderilmez. Claude ya da ChatGPT'ye yazdıklarınız ve
  yüklediğiniz dosyalar o hizmetin kendi gizlilik koşullarına tabidir.
- **Sipariş dökümü yüklemeden önce müşteri adı, telefon ve adres sütunlarını silin.** Bölge analizi
  için yalnızca il ve ilçe yeterlidir. Müşterilerinizin kişisel verilerini bir yapay zekâ hizmetine
  yüklemek KVKK kapsamında sizin sorumluluğunuzdadır.
- Verilerinizin bilgisayarınızdan hiç çıkmamasını istiyorsanız araçları kendi bilgisayarınızda
  çalıştırabilirsiniz; her aracın sayfasında komutları yazılıdır.

## Bilmeniz gereken sınırlar

- Komisyon oranları yaklaşıktır; bağlayıcı oran satıcı panelinizdeki sözleşme ekranındadır. Kargo,
  sabit hizmet bedeli, stopaj, reklam ve iade hesaba dahil değildir.
- Analizler verdiğiniz veriyle sınırlıdır; satış adedi ve ciro tahmini içermez.
- Yorum analizi kelime eşleştirmesine dayanır; ironi ve dolaylı anlatımı kaçırabilir.
- Araçlar Trendyol, Hepsiburada, n11 veya Amazon ile bağlantılı değildir ve onlar tarafından
  onaylanmamıştır. Sonuçlar bilgi amaçlıdır.

## Daha fazlası

- Araçları tek tek indirmek için: [Sürümler](https://github.com/Harungokc/eticaret-agentlari/releases/latest)
- İlk aracın ayrıntılı kılavuzu (tarayıcı arayüzü, Google Sheets çıktısı ve grafikler):
  [AYRINTILI-KILAVUZ.md](01-pazar-ve-komisyon-analizcisi/AYRINTILI-KILAVUZ.md) ·
  [PDF](kilavuz/Pazar-ve-Komisyon-Analizcisi-Kilavuz.pdf)
- Claude Code, Cowork ya da Codex ile kurulum: [AGENTS.md](AGENTS.md)
- Sıradaki araçlar: [SERI.md](SERI.md)
- Geliştiriciler için: her araç kendi klasöründe, saf Python (3.10+), ek paket yok.
  Testler: araç klasöründe `python -m unittest`. Paketler: `python paket/paket_olustur.py`.

## Lisans

[MIT](LICENSE). Kullanabilir, değiştirebilir, paylaşabilirsiniz; garanti verilmez.

## Geliştiren

**Harun Gökce** — harungokce70@gmail.com · 0506 155 46 42

İşletmenize özel bir analiz aracı isterseniz ya da kurulumda takıldıysanız yazabilirsiniz.
