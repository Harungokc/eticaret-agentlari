"""Komisyon Tarife Analizcisi — hesaplama çekirdeği.

Kategori ve satış fiyatı verildiğinde her pazaryeri için yaklaşık komisyonu ve satıcının eline
geçen tutarı hesaplar. Oranlar `veri/komisyon.json` içindeki aralıklardan gelir; satıcı kendi
sözleşme oranını verirse o kullanılır.

Bilinçli olarak yapay zekâsız: sonuçtaki her sayı tablodaki bir orandan ve girilen fiyattan
türetilir, hiçbiri tahmin edilmez.
"""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

VERI_YOLU = Path(__file__).parent / "veri" / "komisyon.json"

_TR = str.maketrans("çğıöşüâîû", "cgiosuaiu")


def katla(metin: str) -> str:
    """Türkçe harfleri sadeleştirir, küçültür; eşleştirme için."""
    metin = metin.replace("İ", "i").replace("I", "ı").lower().translate(_TR)
    return re.sub(r"[^a-z0-9 ]+", " ", metin).strip()


def veri_yukle(yol: Path = VERI_YOLU) -> dict:
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


@dataclass
class Eslesme:
    kategori: dict | None
    nasil: str  # "tam" | "kelime" | "benzer" | "yok"
    adaylar: list[str] = field(default_factory=list)


def kategori_bul(metin: str, veri: dict) -> Eslesme:
    """Serbest metni (ör. "kadın sneaker") tablodaki bir kategoriye bağlar.

    Emin olunamayan durumda kategori döndürmez, adayları döndürür: yanlış kategorinin oranıyla
    hesap yapmak, hesap yapmamaktan kötüdür.
    """
    aranan = katla(metin)
    if not aranan:
        return Eslesme(None, "yok")

    sozluk: dict[str, dict] = {}
    for k in veri["kategoriler"]:
        for ad in [k["ad"], k["anahtar"].replace("_", " "), *k["es_anlamlilar"]]:
            sozluk.setdefault(katla(ad), k)

    if aranan in sozluk:
        return Eslesme(sozluk[aranan], "tam")

    # En uzun eş anlamlı önce: "telefon kılıfı", "telefon"dan önce yakalansın.
    kelimeler = set(aranan.split())
    for ad in sorted(sozluk, key=len, reverse=True):
        parcalar = ad.split()
        if all(p in kelimeler for p in parcalar):
            return Eslesme(sozluk[ad], "kelime")

    yakin = difflib.get_close_matches(aranan, list(sozluk), n=3, cutoff=0.8)
    if yakin:
        return Eslesme(sozluk[yakin[0]], "benzer")

    adaylar = difflib.get_close_matches(aranan, list(sozluk), n=5, cutoff=0.65)
    return Eslesme(None, "yok", sorted({sozluk[a]["ad"] for a in adaylar}))


@dataclass
class Satir:
    pazaryeri: str
    ad: str
    oran_min: float | None
    oran_max: float | None
    kaynak: str  # "tablo" | "satıcının girdiği oran" | "veri yok"
    ek_kesinti_orani: float = 0.0
    komisyon_min: float | None = None
    komisyon_max: float | None = None
    ele_gecen_min: float | None = None
    ele_gecen_max: float | None = None
    kar_min: float | None = None
    kar_max: float | None = None
    notu: str = ""
    kaynak_adresleri: list[str] = field(default_factory=list)

    @property
    def ele_gecen_orta(self) -> float | None:
        if self.ele_gecen_min is None:
            return None
        return (self.ele_gecen_min + self.ele_gecen_max) / 2


def analiz_et(
    kategori: dict,
    fiyat: float,
    veri: dict,
    maliyet: float | None = None,
    kendi_oranlari: dict[str, float] | None = None,
) -> list[Satir]:
    """Her pazaryeri için komisyon ve ele geçen tutarı hesaplar; en çok kazandırandan başlayarak sıralar."""
    if fiyat <= 0:
        raise ValueError("Satış fiyatı sıfırdan büyük olmalı.")
    kendi_oranlari = kendi_oranlari or {}
    satirlar: list[Satir] = []

    for anahtar, pz in veri["pazaryerleri"].items():
        tablo = kategori["oranlar"].get(anahtar)
        if anahtar in kendi_oranlari:
            omin = omax = float(kendi_oranlari[anahtar])
            kaynak, adresler = "satıcının girdiği oran", []
        elif tablo:
            omin, omax = float(tablo["min"]), float(tablo["max"])
            kaynak = "tablo"
            adresler = [veri["kaynaklar"][k]["url"] for k in tablo.get("kaynak", []) if k in veri["kaynaklar"]]
        else:
            satirlar.append(Satir(anahtar, pz["ad"], None, None, "veri yok", notu=pz.get("not", "")))
            continue

        ek = float(pz.get("ek_kesinti_orani", 0.0))
        s = Satir(anahtar, pz["ad"], omin, omax, kaynak, ek, notu=pz.get("not", ""), kaynak_adresleri=adresler)
        s.komisyon_min = round(fiyat * omin / 100, 2)
        s.komisyon_max = round(fiyat * omax / 100, 2)
        ek_tutar = fiyat * ek / 100
        # En yüksek komisyon en düşük ele geçeni verir.
        s.ele_gecen_min = round(fiyat - s.komisyon_max - ek_tutar, 2)
        s.ele_gecen_max = round(fiyat - s.komisyon_min - ek_tutar, 2)
        if maliyet is not None:
            s.kar_min = round(s.ele_gecen_min - maliyet, 2)
            s.kar_max = round(s.ele_gecen_max - maliyet, 2)
        satirlar.append(s)

    satirlar.sort(key=lambda s: (s.ele_gecen_orta is None, -(s.ele_gecen_orta or 0)))
    return satirlar


def kesin_mi(satirlar: list[Satir]) -> bool:
    """İlk sıradaki pazaryeri, ikinciden aralıklar çakışmayacak kadar mı iyi?"""
    dolu = [s for s in satirlar if s.ele_gecen_min is not None]
    if len(dolu) < 2:
        return False
    return dolu[0].ele_gecen_min > dolu[1].ele_gecen_max
