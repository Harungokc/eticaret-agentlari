"""Ürün yorumlarından müşterinin ne istediğini çıkarır: konular, şikâyetler, övgüler ve talepler.

Araç hiçbir siteye bağlanmaz; yorumları kullanıcı verir. Buradaki sayımlar kelime eşleştirmesine
dayanır: hızlıdır ve aynı girdiye hep aynı sonucu verir, ama dili bir insan gibi anlamaz. Bu yüzden
her sayının yanında yorumlardan alıntılar da verilir; son yorumu onları okuyan yapar.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

EN_AZ_YORUM = 5
ALINTI_UZUNLUGU = 180

# Konu → aranacak kelime kökleri ve söz öbekleri (küçük harf). Kök, kelimenin başında aranır.
KONULAR: dict[str, tuple[str, ...]] = {
    "Kargo ve teslimat": ("kargo", "teslim", "gönderim", "kurye", "geç geldi", "geç ulaş", "hızlı geldi", "elime ulaş", "elime geç"),
    "Paketleme": ("paket", "ambalaj", "kutu", "poşet", "koli", "özensiz", "özenli"),
    "Kalite ve malzeme": ("kalite", "malzeme", "kumaş", "dikiş", "sağlam", "dayanık", "işçilik", "plastik", "incecik", "çürük"),
    "Beden, ölçü ve kalıp": ("beden", "kalıp", "numara", "ölçü", "büyük geldi", "küçük geldi", "dar geldi", "bol geldi",
                             "kısa geldi", "uzun geldi", "tam oldu", "tam geldi"),
    "Fiyat": ("fiyat", "pahalı", "ucuz", "indirim", "parasını hak", "paranıza", "parama"),
    "Görsel ve renk uyumu": ("renk", "reng", "görsel", "fotoğraf", "resimde", "resimdeki", "göründüğü", "tonu"),
    "Koku": ("koku",),
    "Dayanma ve arıza": ("bozul", "kırıl", "yırtıl", "soldu", "sökül", "elimde kaldı", "koptu", "kopuyor", "arıza", "çalışmıyor", "çalışmadı", "kalıcı", "döküld",
                         "çatlad", "tüylen"),
    "Kullanım": ("kullanım", "kullanışlı", "kullanışsız", "kurulum", "pratik", "kullanması"),
    "Satıcı ve iletişim": ("satıcı", "mağaza", "iletişim", "cevap", "muhatap", "hediye"),
    "İade ve değişim": ("iade", "değişim", "geri gönder"),
    "Eksik, yanlış ya da hasarlı ürün": ("eksik", "yanlış ürün", "farklı ürün", "hasarlı", "kırık", "defolu", "ezik", "ezilmiş",
                                         "lekeli", "sahte", "orijinal", "çakma"),
}

OLUMSUZ = ("kötü", "berbat", "rezalet", "pişman", "memnun değil", "memnun kalmad", "beğenmed", "tavsiye etmem", "tavsiye etmiyorum",
           "almayın", "bozuk", "kırık", "defolu", "sahte", "çakma", "hayal kırıklığı", "vasat", "işe yaramaz", "geç geldi", "geç ulaş",
           "hasarlı", "ezik", "ezilmiş", "yırtık", "lekeli", "küçük geldi", "büyük geldi", "dar geldi", "bol geldi", "kısa geldi",
           "uzun geldi", "pahalı", "özensiz", "eksik", "yanlış", "maalesef", "bozuld", "sızdır", "akıtıyor", "damlat", "soyul", "çizil", "göçük", "sökül", "bozul", "kırıl", "yırtıl", "elimde kaldı", "koptu", "kopuyor",
           "su geçir", "ıslan",
           "kırıld", "yırtıld", "soldu", "söküld", "çalışmıyor", "çalışmadı", "kalitesiz", "kullanışsız", "değmez", "beklediğim gibi değil",
           "iade ett", "iade ed", "çürük", "incecik", "döküld", "çatlad", "kötü kok")
OLUMLU = ("harika", "mükemmel", "çok güzel", "bayıld", "memnun kaldı", "memnunum", "tavsiye eder", "tavsiye ediyorum", "beğendi",
          "teşekkür", "süper", "kaliteli", "çok iyi", "çok beğen", "şahane", "kusursuz", "sorunsuz", "hızlı geldi", "özenli", "tam oldu",
          "tam geldi", "parasını hak", "çok şık", "güzel kok", "kullanışlı", "sağlam")
TALEP = ("keşke", "olsaydı", "olsa daha", "olsa çok", "olabilirdi", "olmalıydı", "olması gerek", "olsa iyi", "tek eksi", "tek kusur",
         "tek sorun", "tek sıkıntı", "tek olumsuz", "geliştiril", "beklerdim", "isterdim", "eklenebilir", "eklense", "eklenmeli",
         "konulsa", "koysalar", "yapsalar", "daha büyük ol", "daha küçük ol", "daha kalın ol", "daha uzun ol", "daha kaliteli ol",
         "daha sağlam ol", "seçeneği ol", "daha iyi olur", "iyi olurdu", "güzel olurdu", "olsa süper")
# Olumsuz bir fiille birlikte geçince anlamı olumluya dönen sorun adları: "sorun yaşamadım", "koku yapmıyor"
SORUN_ADI = ("sorun", "sıkıntı", "problem", "şikayet", "şikâyet", "koku yap", "leke", "hasar", "pişman")
# Kendisi olumsuzlanınca olumlu olan sorun fiilleri: "sızdırmıyor", "bozulmadı"
SORUN_FIILI = ("bozul", "kırıl", "yırtıl", "sökül", "sızdır", "akıt", "damlat", "sol", "çizil", "soyul", "tüylen", "dökül")
_OLUMSUZ_FIIL = re.compile(r"([a-zçğıöşü]+?)(?:m[ıiuü]yor(?:um|sun|uz|lar)?|m[ae]d[ıi](?:m|n|k|lar|ler)?|m[ae]m[ıi]ş|m[ae]z)"
                           r"(?![a-zçğıöşü])")
# "güzel ama kargo geç geldi" gibi cümleleri iki ayrı parçaya ayırmak için; yakalanan grup karşıtlık bağlacıdır
_BAGLAC = re.compile(r"\s+(ama|fakat|ancak|lakin|yalnız|ne yazık ki)\s+|\s*[.!?…\n;]+\s*")
_KELIME = re.compile(r"[a-zçğıöşüâîû0-9]+")
ETKISIZ = frozenset("""ve veya ile ama fakat ancak bir bu şu o da de ki mi mı mu mü için çok daha en gibi kadar ben biz siz onlar
    ne nasıl neden çünkü her hiç ya hem ise değil var yok olan olarak oldu olur ürün ürünü ürünün ürünler aldım aldık geldi
    gayet biraz bile diye sonra önce şey göre bana bize beni bunu buna bunun onu ona hala artık sadece tek iyi güzel kötü
    ettim ediyorum etti olsun yine zaten tam tane kere defa gün hafta ay keşke olsaydı olsa olurdu olması olmuş
    geliyor içinden içinde başladı gerekiyor yoksa fazla kısmı kısmının bana hâlâ halen istedim yazdım aldı verdi""".split())


def kucult(metin: str) -> str:
    """Türkçe'ye uygun küçük harf: İ → i, I → ı."""
    return metin.replace("İ", "i").replace("I", "ı").lower().replace("’", "'")


@dataclass
class Yorum:
    metin: str
    puan: int | None = None


@dataclass
class Parca:
    """Bir yorumun tek bir düşünce taşıyan parçası (cümle ya da 'ama'dan sonrası)."""
    metin: str
    yorum_no: int
    konular: list[str]
    duygu: str  # "şikâyet", "övgü", "nötr"
    talep: bool


@dataclass
class KonuOzeti:
    ad: str
    yorum_sayisi: int  # bu konudan söz eden yorum
    sikayet: int  # bu konuda şikâyet içeren yorum
    ovgu: int
    sikayet_ornekleri: list[str]
    ovgu_ornekleri: list[str]


@dataclass
class Rapor:
    yorum_sayisi: int
    puanli: int
    puan_dagilimi: dict[int, int]
    ortalama_puan: float | None
    olumlu: int
    notr: int
    olumsuz: int
    puansiz_siniflanan: int  # puanı olmadığı için kelimelerden sınıflanan yorum
    konular: list[KonuOzeti]  # şikâyeti çok olan önce
    talepler: list[tuple[str, list[str]]]  # (cümle, konular)
    talep_iceren_yorum: int
    olumsuz_kelimeler: list[tuple[str, int]]
    konusuz_sikayetler: list[str]  # hiçbir konuya girmeyen şikâyet cümleleri
    etiketler: list[dict]  # her yorum için: duygu, konular, şikâyet konuları, talep
    uyarilar: list[str] = field(default_factory=list)


def _var(kucuk: str, kaliplar: tuple[str, ...]) -> bool:
    return any(re.search(r"(?<![a-zçğıöşüâîû])" + re.escape(k), kucuk) for k in kaliplar)


def _kisalt(metin: str) -> str:
    metin = " ".join(metin.split())
    return metin if len(metin) <= ALINTI_UZUNLUGU else metin[:ALINTI_UZUNLUGU - 1].rstrip() + "…"


def _yorum_duygusu(yorum: Yorum, kucuk: str) -> tuple[str, bool]:
    """(duygu, puandan mı geldi)"""
    if yorum.puan is not None:
        return ("olumsuz" if yorum.puan <= 2 else "nötr" if yorum.puan == 3 else "olumlu"), True
    sayim = Counter()
    for dilim in _BAGLAC.split(kucuk)[::2]:
        eksi, arti = _isaretler(dilim or "")
        sayim["eksi"] += eksi
        sayim["arti"] += arti
    return ("olumsuz" if sayim["eksi"] > sayim["arti"] else "olumlu" if sayim["arti"] > sayim["eksi"] else "nötr"), False


def konu_listesi(ek_konular: dict[str, list[str]] | None = None) -> dict[str, tuple[str, ...]]:
    """Hazır konulara, kullanıcının bu ürün için tanımladığı konuları ekler (ör. "Kapak ve sızdırma": kapak, sızdır)."""
    konular = dict(KONULAR)
    for ad, kelimeler in (ek_konular or {}).items():
        ad = " ".join(re.sub(r"[*?~\[\]]", " ", ad).split())
        kaliplar = tuple(k for k in (kucult(k).strip() for k in kelimeler) if len(k) >= 2)
        if not ad or not kaliplar:
            raise ValueError("Ek konu şu biçimde verilmeli: Konu adı=kelime1,kelime2")
        konular[ad] = tuple(dict.fromkeys(konular.get(ad, ()) + kaliplar))
    return konular


def _isaretler(k: str) -> tuple[bool, bool]:
    """Küçük harfli bir parça için (olumsuz işaret var mı, olumlu işaret var mı). Virgülle ayrılan her bölüme ayrı bakılır."""
    eksi = arti = False
    for bolum in k.split(","):
        sorun_adi = _var(bolum, SORUN_ADI) and not _var(bolum, ("sorunsuz", "sıkıntısız", "problemsiz", "hasarsız", "lekesiz"))
        fiiller = [m.group(1) for m in _OLUMSUZ_FIIL.finditer(bolum)]
        if fiiller and all(sorun_adi or f.startswith(SORUN_FIILI) for f in fiiller):
            arti = True  # "hiç sorun yaşamadım", "sızdırmıyor", "koku yapmıyor"
            continue
        eksi = eksi or _var(bolum, OLUMSUZ) or sorun_adi or bool(fiiller)
        arti = arti or _var(bolum, OLUMLU)
    return eksi, arti


def parcala(yorumlar: list[Yorum], konu_sozlugu: dict[str, tuple[str, ...]] | None = None) -> list[Parca]:
    konu_sozlugu = konu_sozlugu or KONULAR
    parcalar = []
    for no, y in enumerate(yorumlar):
        dilimler = _BAGLAC.split(y.metin)  # [metin, bağlaç ya da None, metin, ...]
        for i in range(0, len(dilimler), 2):
            ham = (dilimler[i] or "").strip(" ,-–—:")
            karsitlik = i > 0 and dilimler[i - 1] is not None  # "… ama" sonrasında gelen parça
            if len(ham) < 3:
                continue
            k = kucult(ham)
            konular = [ad for ad, kaliplar in konu_sozlugu.items() if _var(k, kaliplar)]
            talep = _var(k, TALEP)
            eksi, arti = _isaretler(k)
            if eksi and not arti:
                duygu = "şikâyet"
            elif talep:
                duygu = "nötr"  # "keşke daha sağlam olsaydı" bir övgü değildir; talepler ayrıca listelenir
            elif arti and not eksi:
                duygu = "övgü"
            elif eksi and arti:
                duygu = "nötr"
            elif y.puan is not None and y.puan <= 2:
                duygu = "şikâyet"  # düşük puanlı yorumda geçen, açık övgü içermeyen söz
            elif karsitlik:
                duygu = "şikâyet"  # "güzel ama kapağı zor açılıyor": "ama"dan sonrası çoğunlukla çekincedir
            elif y.puan is not None and y.puan >= 4:
                duygu = "övgü"
            else:
                duygu = "nötr"
            parcalar.append(Parca(ham, no, konular, duygu, talep))
    return parcalar


def analiz_et(yorumlar: list[Yorum], ek_konular: dict[str, list[str]] | None = None) -> Rapor:
    yorumlar = [y for y in yorumlar if y.metin and len(y.metin.strip()) >= 3]
    if len(yorumlar) < EN_AZ_YORUM:
        raise ValueError(f"Bu analiz için en az {EN_AZ_YORUM} yorum gerekir; okunabilen {len(yorumlar)} yorum var")
    n = len(yorumlar)
    puanlar = [y.puan for y in yorumlar if y.puan is not None]
    duygular = [_yorum_duygusu(y, kucult(y.metin)) for y in yorumlar]
    konu_sozlugu = konu_listesi(ek_konular)
    parcalar = parcala(yorumlar, konu_sozlugu)

    konular = []
    for ad in konu_sozlugu:
        ilgili = [p for p in parcalar if ad in p.konular]
        if not ilgili:
            continue
        sikayetler = [p for p in ilgili if p.duygu == "şikâyet"]
        ovguler = [p for p in ilgili if p.duygu == "övgü"]
        konular.append(KonuOzeti(
            ad=ad,
            yorum_sayisi=len({p.yorum_no for p in ilgili}),
            sikayet=len({p.yorum_no for p in sikayetler}),
            ovgu=len({p.yorum_no for p in ovguler}),
            sikayet_ornekleri=[_kisalt(p.metin) for p in sikayetler[:3]],
            ovgu_ornekleri=[_kisalt(p.metin) for p in ovguler[:2]],
        ))
    konular.sort(key=lambda k: (-k.sikayet, -k.yorum_sayisi))

    talep_parcalari = [p for p in parcalar if p.talep]
    gorulen, talepler = set(), []
    for p in talep_parcalari:
        anahtar = kucult(" ".join(p.metin.split()))
        if anahtar not in gorulen:
            gorulen.add(anahtar)
            talepler.append((_kisalt(p.metin), p.konular))

    # Hazır konulara girmeyen, ürüne özgü sorunları yakalamak için: şikâyet ve taleplerde geçen kelimeler.
    # Ekler yüzünden dağılmasınlar diye kelimeler ilk dört harflerine göre gruplanır (kapak, kapağı, kapaktan).
    yorum_kokleri: dict[int, set[str]] = {}
    bicimler: dict[str, Counter] = {}
    for p in parcalar:
        if p.duygu == "şikâyet" or p.talep:
            for k in _KELIME.findall(kucult(p.metin)):
                if len(k) >= 4 and k not in ETKISIZ and not k.isdigit():
                    yorum_kokleri.setdefault(p.yorum_no, set()).add(k[:4])
                    bicimler.setdefault(k[:4], Counter())[k] += 1
    sayac = Counter(kok for kokler in yorum_kokleri.values() for kok in kokler)
    olumsuz_kelimeler = [(min(bicimler[kok], key=lambda b: (-bicimler[kok][b], len(b))), adet)
                         for kok, adet in sayac.most_common(40) if adet >= 2][:20]

    etiketler = []
    for no, y in enumerate(yorumlar):
        benim = [p for p in parcalar if p.yorum_no == no]
        etiketler.append({
            "duygu": duygular[no][0],
            "konular": sorted({k for p in benim for k in p.konular}),
            "sikayet_konulari": sorted({k for p in benim if p.duygu == "şikâyet" for k in p.konular}),
            "talep": any(p.talep for p in benim),
        })

    r = Rapor(
        yorum_sayisi=n, puanli=len(puanlar),
        puan_dagilimi={s: puanlar.count(s) for s in (5, 4, 3, 2, 1)},
        ortalama_puan=(sum(puanlar) / len(puanlar)) if puanlar else None,
        olumlu=sum(d == "olumlu" for d, _ in duygular), notr=sum(d == "nötr" for d, _ in duygular),
        olumsuz=sum(d == "olumsuz" for d, _ in duygular), puansiz_siniflanan=sum(not p for _, p in duygular),
        konular=konular, talepler=talepler, talep_iceren_yorum=len({p.yorum_no for p in talep_parcalari}),
        olumsuz_kelimeler=olumsuz_kelimeler,
        konusuz_sikayetler=[_kisalt(p.metin) for p in parcalar if p.duygu == "şikâyet" and not p.konular][:10],
        etiketler=etiketler,
    )
    if n < 30:
        r.uyarilar.append(f"Yalnızca {n} yorum var; 30 ve üzeri yorumla sonuçlar daha güvenilir olur.")
    if r.puansiz_siniflanan:
        r.uyarilar.append(f"{r.puansiz_siniflanan} yorumun puanı verilmemiş; bunların olumlu/olumsuz ayrımı kelimelerden yapıldı ve "
                          "daha az güvenilirdir.")
    if puanlar and r.puan_dagilimi[5] + r.puan_dagilimi[4] == len(puanlar):
        r.uyarilar.append("Listede 3 yıldız ve altı yorum yok. Şikâyetleri görmek için düşük puanlı yorumları da ekleyin.")
    return r
