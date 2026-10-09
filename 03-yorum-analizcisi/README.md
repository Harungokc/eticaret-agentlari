# Yorum Analizcisi

Müşterileriniz size ne söylüyor? Bu araç bir ürünün yorumlarını okur ve üç soruyu yanıtlar:

| Soru | Araç ne gösterir |
|---|---|
| **En çok neden şikâyet ediliyor?** | Konu başına şikâyet eden yorum sayısı (kargo, paketleme, kalite, beden… ve ürününüze özgü konular), yorumlardan alıntılarla |
| **Müşteri üründe ne istiyor?** | “Keşke…”, “…olsaydı”, “tek eksiği…” diye başlayan cümlelerin listesi |
| **Neyi beğeniyorlar?** | Konu başına övgü sayıları; ürün açıklamasında öne çıkarabileceğiniz güçlü yanlar |

Kendi ürününüz için kullanırsanız neyi düzelteceğinizi, rakip bir ürün için kullanırsanız onun zayıf
yanını görürsünüz. Sonucu sohbette özetler ve **Excel dosyası** olarak verir. Ücretsiz, açık kaynak
(MIT). Kod bilmeniz gerekmez.

## Claude ya da ChatGPT sohbetinde kullanın

**1. Paketi indirin:** [yorum-analizcisi.zip](https://github.com/Harungokc/eticaret-agentlari/releases/latest/download/yorum-analizcisi.zip) (ZIP'ten çıkarmayın)

**2. Asistanınıza yükleyin:**

| | Nasıl yüklenir |
|---|---|
| **Claude** (claude.ai ya da uygulama) | **Customize → Skills → + → Upload a skill** deyip ZIP dosyasını seçin. Bir kez eklenir, her sohbette hazırdır. *Settings → Capabilities* altında kod yürütme açık olmalıdır. |
| **ChatGPT** | Yeni sohbette ZIP dosyasını ekleyin ve şunu yazın: *"Bu ZIP dosyasını aç, içindeki SKILL.md dosyasını oku ve oradaki talimatlara göre çalış."* |

**3. Yorumları yapıştırın ve sorun.** Ürün sayfasındaki yorumları seçip kopyalayın, sohbete yapıştırın:

> Aşağıda ürünümün yorumları var. Müşteriler en çok neden şikâyet ediyor, üründe ne istiyorlar?
> Neyi geliştirmeliyim?
>
> *(yorumlar)*

Düşük puanlı yorumları da eklemeyi unutmayın; şikâyetler orada.

## Nasıl çalışır

Araç pazaryerlerinden **yorum çekmez**; yorumları siz verirsiniz. İş iki tarafa bölünür:

- **Araç sayar.** Her yorumu cümlelere böler, konulara ayırır, şikâyet mi övgü mü olduğuna bakar ve
  talep cümlelerini toplar. Aynı yorumlara her zaman aynı sayıları verir.
- **Asistan yorumlar.** Sayıları ve alıntıları okuyup size ne yapabileceğinizi anlatır.

Hazır konular geneldir. Ürününüze özgü sorunlar (bir termosta “kapak”, bir ayakkabıda “taban”)
şikâyetlerde sık geçen kelimelerden bulunur ve ayrı bir konu olarak saydırılır; asistan bunu
kendiliğinden yapar.

## Örnek sonuç

Uydurma 40 termos yorumuyla:

```
YORUM ANALİZİ — 40 yorum
  Ortalama puan: 3,6 (40 puanlı yorum)   5★ 16  4★ 9  3★ 5  2★ 5  1★ 5
  Olumlu 25 (%62)   Nötr 5 (%12)   Olumsuz 10 (%25)

KONULAR (şikâyeti çok olan önce; sayılar yorum adedidir)
  Kapak ve sızdırma                  söz eden   7   şikâyet   6   övgü   0
  Paketleme                          söz eden   7   şikâyet   3   övgü   4
  İade ve değişim                    söz eden   3   şikâyet   3   övgü   0
  Eksik, yanlış ya da hasarlı ürün   söz eden   3   şikâyet   3   övgü   0
  Kalite ve malzeme                  söz eden   9   şikâyet   2   övgü   7
  Kargo ve teslimat                  söz eden   5   şikâyet   2   övgü   3
  Satıcı ve iletişim                 söz eden   5   şikâyet   2   övgü   3
  Kullanım                           söz eden   4   şikâyet   2   övgü   2
  Görsel ve renk uyumu               söz eden   3   şikâyet   1   övgü   2
  Fiyat                              söz eden   2   şikâyet   1   övgü   1
  Koku                               söz eden   2   şikâyet   1   övgü   1
  Dayanma ve arıza                   söz eden   1   şikâyet   1   övgü   0

EN ÇOK ŞİKÂYET EDİLENLER
  Kapak ve sızdırma — 6 yorum
    “kapağı biraz zor açılıyor”
    “İlk hafta iyiydi sonra kapaktan sızdırmaya başladı”
    “Kapağın contası ikinci haftada çıktı, sızdırıyor”
  Paketleme — 3 yorum
    “Kutu ezik geldi, termosun altı da göçük”
    “Paketleme çok özensiz”
    “Kutusu açılmış gibiydi, içinden kullanım kılavuzu da çıkmadı”
  İade ve değişim — 3 yorum
    “İade ettim”
    “Değişim istedim hâlâ bekliyorum”
    “İade sürecinde de satıcı ilgilenmedi”
  Eksik, yanlış ya da hasarlı ürün — 3 yorum
    “Kutu ezik geldi, termosun altı da göçük”
    “Eksik ürün gönderilmiş”
    “Kargo firması paketi ezmiş, hasarlı geldi”

MÜŞTERİ TALEPLERİ — 7 yorumda
  “Keşke tek elle açılabilen bir kapak olsaydı”  [Kapak ve sızdırma]
  “Tek eksiği bardak kısmının küçük olması”
  “Keşke 750 ml seçeneği de olsaydı, 500 ml bana az geliyor”
  “Boyası çizilmeye biraz müsait, bir kılıfı olsa çok iyi olurdu”
  “Tek kusuru ağzının dar olması, buz atılamıyor”
  “Kapak contası yedeği ile gelse daha iyi olurdu”  [Kapak ve sızdırma]
  “Keşke taşıma askısı olsaydı”
```

## Kendi bilgisayarınızda çalıştırmak

Python 3.10 veya üstü yeterlidir; ek paket gerekmez.

```bash
python3 agent.py analiz ornek/ornek_yorumlar.csv
python3 agent.py analiz yorumlar.csv --konu "Kapak ve sızdırma=kapak,kapağ,sızdır" --excel sonuc.xlsx
python3 agent.py konular     # hazır konu başlıkları
python3 -m unittest          # testler
```

Yorum dosyası `yorum;puan` başlıklı bir CSV ([şablon](ornek/sablon.csv)) ya da her satırı bir yorum
olan bir `.txt` dosyası olabilir.

## Bilmeniz gereken sınırlar

- Araç kelime eşleştirir; ironi, yazım hatası ve dolaylı anlatımı kaçırabilir. Sayıları yanlarındaki
  alıntılarla birlikte değerlendirin.
- Sonuçlar verdiğiniz yorumlarla sınırlıdır; yorum yazanlar bütün müşterilerinizi temsil etmeyebilir.
- Yorumlarda kişisel bilgi (ad, telefon, adres) varsa paylaşmadan önce çıkarın.
- Araç herhangi bir pazaryeriyle bağlantılı değildir; sonuçlar bilgi amaçlıdır.

**Geliştiren:** Harun Gökce — harungokce70@gmail.com · 0506 155 46 42
