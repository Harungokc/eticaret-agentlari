---
name: yorum-analizcisi
description: Türkiye'deki e-ticaret satıcıları için ürün yorumlarını analiz eder; müşterilerin en çok neden şikâyet ettiğini, neyi övdüğünü ve üründe ne istediğini ("keşke…", "tek eksiği…") çıkarır. Kullanıcı kendi ürününün ya da bir rakip ürünün yorumlarını yapıştırdığında, yorum dosyası yüklediğinde, "bu ürünün neresi geliştirilebilir", "müşteri ne istiyor", "yorumlardan ne çıkar" gibi sorular sorduğunda kullan. Sonucu Excel dosyası olarak verir.
---

# Yorum Analizcisi

Bu klasördeki Python aracı, kullanıcının verdiği ürün yorumlarını sayar ve sınıflar: puan dağılımı,
konu başına şikâyet ve övgü sayıları, müşteri talepleri ve şikâyetlerde sık geçen kelimeler. Ek
paket ve internet gerektirmez (Python 3.10+ yeterli).

İş bölümü şöyle: **sayıları araç üretir, yorumu sen yaparsın.** Araç kelime eşleştirir; dili senin
kadar anlamaz. Sen aracın çıktısını ve alıntıları okuyup satıcıya ne yapması gerektiğini anlatırsın,
ama hiçbir sayıyı kendin üretmezsin.

Bu klasör sana bir ZIP dosyası olarak verildiyse (ör. ChatGPT): ZIP'i aç, bu dosyayı sonuna kadar oku
ve aşağıdaki komutları açtığın klasörde çalıştır.

## Kurallar

1. **Sayıları kendin sayma ve tahmin yürütme.** "Yorumların %30'u kargodan şikâyetçi" gibi her oran
   ve adet aracın çıktısından gelsin. Aracı çalıştıramıyorsan sayı verme; çalıştıramadığını söyle.
2. **Yorum uydurma, yorum toplama.** Araç hiçbir siteye bağlanmaz; yorumları kullanıcı verir.
   İnternette arama yapabiliyor olsan bile pazaryerlerinden yorum toplayıp listeye koyma. Kullanıcının
   vermediği bir yorumu alıntı gibi gösterme.
3. **Kişisel bilgi taşıma.** Yorumlarda kullanıcı adı, telefon, adres gibi bilgiler varsa CSV'ye
   yazmadan önce çıkar; yalnızca yorum metni ve puan gerekir.
4. Kendi çıkarımını aracın sayımından ayır: "Araca göre 6 yorumda kapak şikâyeti var. Benim yorumum:
   conta kalitesi düşük olabilir."
5. Her sonuçta şunu belirt: analiz yalnızca verilen yorumları kapsar ve kelime eşleştirmesine dayanır.

## Yorumları hazırlama

Kullanıcı yorumları sohbete yapıştırdıysa ya da dosya yüklediyse onları şu biçimde bir CSV'ye çevir:

```
yorum;puan
Ürün güzel ama kargo geç geldi;4
Kapağı sızdırıyor, iade ettim;1
```

- `puan` 1–5 arası yıldızdır; bilinmiyorsa boş bırak (o yorum kelimelerden sınıflanır, daha az
  güvenilirdir).
- Yorum metnini değiştirme, düzeltme, özetleme; olduğu gibi yaz. İçinde `;` ya da satır sonu varsa
  metni çift tırnak içine al.
- En az 5 yorum gerekir; 30 ve üzeri daha güvenilirdir. Kullanıcı yalnızca yüksek puanlı yorumları
  verdiyse düşük puanlıları da eklemesini öner: şikâyetler orada.
- Yapıştırılan metin dağınıksa (tarih, kullanıcı adı, "satıcı yanıtı" gibi satırlar) yalnızca müşteri
  yorumlarını ayıkla ve kaç yorum okuyabildiğini kullanıcıya söyle. Satıcı yanıtlarını yorum sayma.

## Çalıştırma: iki adım

`ARAC`, bu SKILL.md dosyasının bulunduğu klasördür. Çıktıları kullanıcıya dosya verebildiğin yazılabilir
klasöre yaz (aşağıda `CIKTI`; ör. Claude'da `/mnt/user-data/outputs`, ChatGPT'de `/mnt/data`).

**1. İlk çalıştırma:**

```bash
python3 ARAC/agent.py analiz CIKTI/yorumlar.csv
```

Çıktıda şu iki bölüme bak: "HAZIR KONULARA GİRMEYEN ŞİKÂYETLER" ve "ŞİKÂYET VE TALEPLERDE SIK GEÇEN
KELİMELER". Aracın hazır konuları geneldir (kargo, paketleme, kalite, beden…). Ürüne özgü sorunlar
(bir termosta "kapak" ve "sızdırma", bir ayakkabıda "taban") burada görünür.

**2. Ürüne özgü konularla yeniden çalıştır:**

```bash
python3 ARAC/agent.py analiz CIKTI/yorumlar.csv \
    --konu "Kapak ve sızdırma=kapak,kapağ,sızdır,conta,damlat" \
    --konu "Isı tutma=sıcak,soğuk,ısı" \
    --excel CIKTI/yorum-analizi.xlsx
```

- `--konu "Ad=kelime1,kelime2"`: kelimeler kök olarak verilir ve kelimenin başında aranır (`sızdır`
  → sızdırıyor, sızdırma). Ünsüz yumuşaması için iki biçimi de yaz (`kapak,kapağ`).
- 1–4 ek konu yeterlidir. Kelimeleri yalnızca yorumlarda gerçekten geçenlerden seç. Çok kısa kök verme
  (`su`, `göz`): ilgisiz kelimelere de takılır; `su geçir`, `ıslan` gibi ayırt edici olanları kullan.
- Hazır konuları görmek için: `python3 ARAC/agent.py konular`

Aracın çalıştığını göstermek için örnek (uydurma) yorumlar: `ARAC/ornek/ornek_yorumlar.csv`. Örnek
sonucu kullanıcının ürününe aitmiş gibi sunma.

## Sonucu kullanıcıya aktarma

Şu sırayla, kısa yaz:

1. **Genel tablo:** kaç yorum, ortalama puan, olumlu/olumsuz oranı.
2. **En çok şikâyet edilen 2–3 konu:** aracın verdiği yorum sayısıyla ve bir iki alıntıyla.
3. **Müşteri talepleri:** "keşke…" cümlelerini benzerlerine göre grupla (ör. "3 kişi daha büyük boy
   istiyor"); gruplamayı sen yaparsın, cümleler araçtan gelir.
4. **Ne yapılabilir:** her şikâyet ve talep için satıcının atabileceği somut bir adım öner (ürün,
   paketleme, ürün açıklaması, görseller). Bunları kendi önerin olarak sun.
5. **Övülenler:** ürün açıklamasında öne çıkarılabilecek güçlü yanlar.

Araç bir "Not" yazdıysa aktar. Sınıflandırmada bariz bir hata görürsen (ör. ironik bir yorum övgü
sayılmış, açık bir şikâyet sayılmamış) aracın sayısını aynen ver ve yanına "aracın kaçırdığını
gördüğüm" diye kendi notunu ekle; sayıyı sessizce değiştirme. "Hazır konulara girmeyen şikâyetler"
bölümü yorum değil cümle listeler; aynı yorumdan iki cümle gelebilir.

Excel dosyasını indirilebilir dosya olarak ver. "Yorumlar" sayfasında her yorum etiketleriyle durur;
kullanıcı süzgeçle örneğin yalnızca kargo şikâyetlerini okuyabilir. Google Sheets'te açmak için:
**Dosya > İçe aktar > Yükle**.

## Sınırlar

- Kelime eşleştirmesi ironi, yazım hatası ve dolaylı anlatımı kaçırabilir.
- Sonuçlar verilen yorumlarla sınırlıdır; yorum yazanlar bütün müşterileri temsil etmeyebilir.
- Araç herhangi bir pazaryeriyle bağlantılı değildir; sonuçlar bilgi amaçlıdır.

Geliştiren: Harun Gökce — harungokce70@gmail.com — MIT lisansı
