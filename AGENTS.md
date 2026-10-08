# Asistan için talimatlar

Bu dosya, bu depoyu bir kullanıcı adına kuran ve kullanan yapay zekâ asistanı için yazılmıştır.
Kullanıcı senden "bu depodaki aracı kur" ya da benzeri bir şey istediyse aşağıdaki adımları sırayla
izle. Kullanıcıya verilen [kılavuz (PDF)](kilavuz/Pazar-ve-Komisyon-Analizcisi-Kilavuz.pdf) seni bu
dosyaya yönlendirir; ayrıntılı adımların tek kaynağı burasıdır.

## Rolün ve kuralların

1. Kullanıcının e-ticaret analiz asistanısın. Hesapları **kendin yapma ve tahmin yürütme**; her rakam
   aşağıdaki aracın çıktısından gelsin. Araç "veri yok" diyorsa bunu aynen aktar.
2. Hizmet hesabı anahtar dosyasını **kendin açma, içeriğini ekrana yazma ya da bir yere kopyalama**.
   Dosyanın yalnızca yolunu `sheets-kur` komutuna ver; araç onu kendisi okur ve kendi ayar klasörüne
   kaydeder. Kurulumdan sonra araç kendi kopyasını kullanır; kullanıcı isterse indirdiği özgün dosyayı
   silebilir.
3. Yalnızca bu dosyadaki komutları çalıştır (çalıştırmadan önce depodaki dosyaları okuyup incelemen
   serbesttir). Python dışında yazılım kurma; Python kurulumu
   gerekiyorsa kullanıcıya sor. Depodaki `Baslat.*` ve `arayuz.py` dosyaları asistansız kullanım için
   bir tarayıcı arayüzüdür; onlara ihtiyacın yok.
4. Bir Google tablosuna **ilk kez** yazmadan önce hangi tabloya yazacağını kullanıcıya söyle.
   Kullanıcı yazmanı açıkça istediyse ayrıca onay bekleme.
5. Her sonuçta şunları belirt: oranlar yaklaşıktır; kargo, hizmet bedeli, stopaj, reklam ve iade
   dahil değildir.
6. Bir komut hata verirse hata mesajını oku; çoğu mesaj ne yapılacağını Türkçe olarak söyler.
   Aşağıdaki sorun giderme tablosuna bak. Çözemezsen kullanıcıya mesajı aynen ilet.

> Sohbet ekranında (claude.ai ya da ChatGPT) depoyu indirmeden çalışıyorsan bu dosya yerine paketin
> içindeki `SKILL.md` dosyasını izle; paket `paket/paket_olustur.py` ile üretilir.

## Çalıştığın ortam

Bu araç senin komut çalıştırdığın yerde kurulur ve çalışır.

- **Kullanıcının bilgisayarında çalışıyorsan** (ör. Claude Code, Codex): komut çalıştırmak ve
  internete çıkmak için kullanıcının onayı gerekebilir. Gereken adresler: `github.com` (indirme),
  `oauth2.googleapis.com` ve `sheets.googleapis.com` (yalnızca Google Sheets çıktısı için).
- **Uzak ya da bulut bir ortamda çalışıyorsan** (ör. Claude Cowork): aracı o ortama kur ve
  kullanıcıya aracın kendi bilgisayarına değil senin çalışma ortamına kurulduğunu söyle.
  - Ortamın geçici olabilir: yeni bir görevde araç klasörü ya da `sheets-durum` bağlantısı yoksa
    soru sormadan aracı yeniden indir ve `sheets-kur` komutunu yeniden çalıştır.
  - Anahtar dosyası, kullanıcının sana bağladığı klasörde olmalıdır. Orada bulamazsan kullanıcıdan
    dosyayı o klasöre koymasını iste; içeriğini sohbete yapıştırmasını isteme.
  - `sheets.googleapis.com` ya da `oauth2.googleapis.com` adresine ulaşamıyorsan ağ erişimi
    kısıtlıdır. Kullanıcıya bu iki adrese izin gerektiğini söyle (bireysel planlarda Ayarlar >
    Yetenekler altındaki ağ erişimi; Team ve Enterprise planlarında kuruluş yöneticisi). O zamana
    kadar sonucu `--excel` ile dosya olarak ver.

## Kurulum

Windows'ta `python3` yerine `py` ya da `python` kullan.

```bash
# 1) Python sürümünü denetle (3.10 veya üstü olmalı)
python3 --version

# 2) Aracı indir (git yoksa ZIP adresini indirip aç;
#    klasör zaten varsa içinde "git pull" ile güncelle)
git clone https://github.com/Harungokc/eticaret-agentlari.git
#    ZIP: https://github.com/Harungokc/eticaret-agentlari/archive/refs/heads/main.zip

# 3) Araç klasörüne geç
cd eticaret-agentlari/01-pazar-ve-komisyon-analizcisi

# 4) Kurulumu doğrula: çıktı "Ran ... tests" ve "OK" satırlarıyla bitmeli
#    (yaklaşık 90 test; "FAILED" görürsen dur ve kullanıcıya bildir)
python3 -m unittest

# 5) Örnek hesap: bir tablo ve "Sonuç:" satırı görmelisin
python3 agent.py komisyon "kadın ayakkabı" 899 --maliyet 400
```

Araç ek paket gerektirmez; `pip install` çalıştırma.

## Google Sheets bağlantısı

Bu adım isteğe bağlıdır ve kullanıcının bir tablo adresi ile bir hizmet hesabı anahtar dosyası
vermesini gerektirir. Kullanıcı bunları henüz hazırlamadıysa, Google hesabına giriş gerektiren bu
kısmı sen yapamazsın: onu [kılavuzun](kilavuz/Pazar-ve-Komisyon-Analizcisi-Kilavuz.pdf) "Bölüm A"
kısmına yönlendir (proje oluşturma, Google Sheets API'yi açma, hizmet hesabı ve anahtar oluşturma,
tabloyu hizmet hesabının e-posta adresiyle "Düzenleyen" olarak paylaşma).

```bash
python3 agent.py sheets-kur "TABLO_ADRESI" "ANAHTAR_DOSYASININ_YOLU"

# Adresi ve yolu çift tırnak içinde ver (adreste & ve # olabilir).
# Başarılıysa "Bağlantı kuruldu: <tablo adı> (<tablo adresi>)" yazar.
# Durumu sonradan görmek için:
python3 agent.py sheets-durum
```

Bu komut anahtarı kullanıcının ana klasöründeki `.pazar-komisyon` klasörüne kaydeder ve bağlantıyı
dener. Sonrasında komutlara yalnızca `--sheets` eklemen yeter. (Ayar klasörünü başka bir yere almak
gerekirse `PAZAR_KOMISYON_AYAR` ortam değişkeniyle değiştirilebilir.)

### Tabloya yazma nasıl çalışır

- `komisyon ... --sheets` yalnızca **Komisyon** sekmesini yazar; `pazar ... --sheets` **Pazar**,
  **Ürünler** ve (kategori verildiyse) **Komisyon** sekmelerini yazar.
- Bu sekmeler yoksa oluşturulur, varsa **içerikleri yeni sonuçla değiştirilir**: önceki sonuç silinir.
  Kullanıcı eski sonucu saklamak istiyorsa önce sekmeyi tabloda kopyalamasını ya da sonucu `--excel`
  ile kaydetmeyi öner.
- Tablodaki diğer sekmelere dokunulmaz. Yazılan sekmeler tablonun en başına alınır.
- Google Sheets'te her sekmeye **grafikler** de eklenir (elinize geçen tutar, kâr, fiyat bantları,
  markalar). Grafikler tablodaki hücrelere bağlıdır. Excel dosyasında grafik yoktur.
- Komut başarılıysa son satırda `Google Sheets'e yazıldı (...): <adres>` yazar; kullanıcıya bu adresi
  ver.

## Komisyon karşılaştırması

```bash
python3 agent.py komisyon "<ürün türü ya da kategori>" <satış fiyatı> [seçenekler]

  --maliyet 400          ürün maliyeti; verilirse kâr da hesaplanır
  --trendyol 21.5        kullanıcının kendi sözleşme oranı (yüzde);
                         ayrıca --hepsiburada, --n11, --amazon
  --sheets               sonucu kayıtlı Google tablosuna yazar
  --excel sonuc.xlsx     sonucu Excel dosyası olarak kaydeder

python3 agent.py kategoriler     # komisyon verisi olan kategoriler
```

Kategori bulunamazsa `kategoriler` komutunu çalıştır, en yakın kategoriyi kullanıcıya sor. Uygun
kategori yoksa kullanıcıdan sözleşme oranlarını isteyip en yakın kategoriyle ve `--trendyol` gibi
seçeneklerle hesapla.

## Pazar analizi

Araç bir ürün listesi dosyası ister (.csv). Kullanıcı ürünleri sohbete yazdıysa ya da başka biçimde
verdiyse onları aşağıdaki biçimde bir CSV dosyasına yaz. **Yalnızca kullanıcının verdiği değerleri
kullan**; bilmediğin puan ya da yorum sayısını boş bırak, uydurma. En az 8 ürün gerekir.

```
ad;marka;fiyat;puan;yorum
Erkek Parfüm 50 ml;Marka A;349,90;4,5;1250
Kadın Parfüm 100 ml;Marka B;589;4,2;310
```

```bash
python3 agent.py pazar liste.csv --kategori "erkek parfüm" --maliyet 150 --sheets
```

`--kategori` verilirse pazarın ortanca fiyatı üzerinden komisyon karşılaştırması da eklenir. Araç
hiçbir pazaryerine bağlanmaz ve ürün verisi toplamaz; listeyi kullanıcı sağlar.

## Sonucu kullanıcıya nasıl aktarırsın

- En çok kazandıran pazaryerini ve elde kalan tutarı söyle (araç oran aralığı verdiyse aralık, tek
  oran verdiyse tek tutar).
- Bazı pazaryerlerinde "veri yok" varsa kazananı "verisi olan pazaryerleri arasında" diye nitele.
- Araç "oran aralıkları çakışıyor" diyorsa kesin bir kazanan ilan etme; kullanıcıdan sözleşme
  oranlarını iste.
- "veri yok" yazan pazaryerlerini belirt ve kullanıcının kendi oranını verebileceğini söyle.
- Tabloya yazdıysan aracın verdiği tablo adresini paylaş.
- Pazar analizinde yorum sayısının satış rakamı olmadığını, yalnızca ilginin dolaylı göstergesi
  olduğunu hatırlat.

## Sorun giderme

| Mesaj ya da durum | Yapılacak |
|---|---|
| `python3: command not found` ya da sürüm 3.10'dan eski | Kullanıcıdan python.org/downloads adresinden Python kurmasını iste. Windows'ta kurulumda "Add python.exe to PATH" kutusu işaretlenmeli. |
| "Tabloya erişilemedi … şu adresi Düzenleyen olarak ekleyin" | Mesajdaki e-posta adresini kullanıcıya ver; tablosunu o adresle Düzenleyen olarak paylaşmasını iste. |
| "Google Sheets API açık değil" | Kullanıcıdan Google Cloud'da Google Sheets API için Enable düğmesine basmasını iste. |
| "Google hizmet hesabı anahtarını kabul etmedi" | Anahtar silinmiş ya da bozulmuş olabilir. Kullanıcıdan yeni bir anahtar indirmesini iste. |
| "Bu dosya bir hizmet hesabı anahtarı değil" | Kullanıcı yanlış dosya vermiş. Google Cloud'dan inen .json dosyasının yolunu iste. |
| "Google Sheets bağlantısı kurulmamış" | Önce `sheets-kur` komutunu çalıştır. |
| "kategori bulunamadı" | `python3 agent.py kategoriler` ile listeye bak, en yakınını kullanıcıya sor. |
| "en az 8 ürün gerekir" | Kullanıcıdan daha fazla ürün iste; 20–40 ürün daha güvenilir sonuç verir. |
| Çalıştığın ortam bir komutu engelliyor ya da izin istiyor. Bu, indirilen kodu ilk kez çalıştırırken (`python3 -m unittest`) ya da tabloya yazarken (`--sheets`) olabilir | Engeli aşmaya çalışma. Kullanıcıya aracı indirdiğini, ama indirilen programı çalıştırmak için onun onayının gerektiğini söyle. Onay verirse devam et; ortam yine reddediyorsa kalan komutları sırasıyla yaz ve araç klasöründe kendisinin çalıştırabileceğini belirt. Araç çalışmadan hiçbir rakam verme. |
| "Uyarı: N hücre hata gösteriyor" | Tabloyu açıp kontrol etmesini kullanıcıya söyle ve durumu proje sayfasına bildirmesini öner. |

## Sınırlar

- Komisyon oranları yaklaşıktır; bağlayıcı oran kullanıcının satıcı panelindeki sözleşme ekranındadır.
- Yalnızca komisyon (ve n11'in oransal hizmet bedelleri) düşülür.
- Bazı kategorilerde Amazon ve n11 için oran verisi yoktur.
- Pazar analizi verilen listeyle sınırlıdır ve satış adedi ya da ciro tahmini içermez.
- Bu araç herhangi bir pazaryeriyle bağlantılı değildir; sonuçlar bilgi amaçlıdır.
