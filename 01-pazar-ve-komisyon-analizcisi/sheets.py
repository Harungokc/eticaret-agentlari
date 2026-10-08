"""Sonuçları bir Google Sheets tablosuna yazar (isteğe bağlı özellik).

Aracın geri kalanı internete bağlanmaz. Bu modül yalnızca kullanıcı bir tablo adresi ve bir hizmet
hesabı anahtarı verdiğinde çalışır ve yalnızca Google'a bağlanır (oauth2.googleapis.com ve
sheets.googleapis.com).

Ek paket kullanılmaz. Google'ın istediği imzalı kimlik belgesi (RS256 JWT) burada standart
kütüphaneyle üretilir.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from excel import (AFIS, BASLIK, DUZ, ETIKET, GIRDI_METIN, GIRDI_TL, GIRDI_YUZDE, NOT, ONDALIK, SARMA, SUTUN, TAM, TL,
                   VURGU_TL, YUZDE, Formul, Sayfa)

KAPSAM = "https://www.googleapis.com/auth/spreadsheets"
API = "https://sheets.googleapis.com/v4/spreadsheets"


class SheetsHatasi(Exception):
    pass


# ---------------------------------------------------------------- anahtar ve imza

def anahtar_oku(yol: str | Path) -> dict:
    yol = Path(yol).expanduser()
    if not yol.exists():
        raise SheetsHatasi(f"Anahtar dosyası bulunamadı: {yol}")
    try:
        anahtar = json.loads(yol.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise SheetsHatasi("Anahtar dosyası okunamadı. Google Cloud'dan indirdiğiniz JSON dosyasını verdiğinizden emin olun.") from None
    if not isinstance(anahtar, dict) or anahtar.get("type") != "service_account" or not anahtar.get("private_key") \
            or not anahtar.get("client_email"):
        raise SheetsHatasi("Bu dosya bir hizmet hesabı anahtarı değil. Google Cloud'da hizmet hesabı için oluşturulan "
                           "JSON anahtar dosyası gerekir.")
    return anahtar


def _der_oku(veri: bytes, konum: int) -> tuple[int, bytes, int]:
    """Bir DER öğesi okur: (etiket, içerik, sonraki konum)."""
    etiket = veri[konum]
    uzunluk = veri[konum + 1]
    konum += 2
    if uzunluk & 0x80:
        n = uzunluk & 0x7F
        uzunluk = int.from_bytes(veri[konum:konum + n], "big")
        konum += n
    return etiket, veri[konum:konum + uzunluk], konum + uzunluk


def _dizi(icerik: bytes) -> list[tuple[int, bytes]]:
    ogeler, konum = [], 0
    while konum < len(icerik):
        etiket, deger, konum = _der_oku(icerik, konum)
        ogeler.append((etiket, deger))
    return ogeler


def rsa_anahtari_coz(pem: str) -> tuple[int, int]:
    """PEM biçimindeki özel anahtardan (n, d) çiftini çıkarır. PKCS#8 ve PKCS#1 kabul edilir."""
    govde = re.sub(r"-----[A-Z ]+-----|\s", "", pem)
    try:
        der = base64.b64decode(govde)
        ust = _dizi(_der_oku(der, 0)[1])
        if len(ust) == 3 and ust[2][0] == 0x04:  # PKCS#8: sürüm, algoritma, içteki anahtar
            ust = _dizi(_der_oku(ust[2][1], 0)[1])
        n, d = int.from_bytes(ust[1][1], "big"), int.from_bytes(ust[3][1], "big")
    except (ValueError, IndexError):
        raise SheetsHatasi("Anahtar dosyasındaki özel anahtar çözülemedi.") from None
    if n.bit_length() < 2048 or d <= 1:
        raise SheetsHatasi("Anahtar dosyasındaki özel anahtar geçersiz.")
    return n, d


_SHA256_ONEKI = bytes.fromhex("3031300d060960864801650304020105000420")


def rs256_imzala(mesaj: bytes, n: int, d: int) -> bytes:
    """RSASSA-PKCS1-v1_5, SHA-256."""
    k = (n.bit_length() + 7) // 8
    ozet = _SHA256_ONEKI + hashlib.sha256(mesaj).digest()
    dolgulu = b"\x00\x01" + b"\xff" * (k - len(ozet) - 3) + b"\x00" + ozet
    return pow(int.from_bytes(dolgulu, "big"), d, n).to_bytes(k, "big")


def _b64(veri: bytes) -> str:
    return base64.urlsafe_b64encode(veri).rstrip(b"=").decode("ascii")


def jwt_olustur(anahtar: dict, simdi: int | None = None) -> str:
    simdi = int(simdi if simdi is not None else time.time())
    hedef = anahtar.get("token_uri") or "https://oauth2.googleapis.com/token"
    baslik = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
    govde = _b64(json.dumps({"iss": anahtar["client_email"], "scope": KAPSAM, "aud": hedef, "iat": simdi,
                             "exp": simdi + 3600}, separators=(",", ":")).encode())
    n, d = rsa_anahtari_coz(anahtar["private_key"])
    return f"{baslik}.{govde}.{_b64(rs256_imzala(f'{baslik}.{govde}'.encode('ascii'), n, d))}"


# ---------------------------------------------------------------- http

def _http(yontem: str, adres: str, govde: bytes | None, basliklar: dict) -> tuple[int, bytes]:
    istek = urllib.request.Request(adres, data=govde, method=yontem, headers=basliklar)
    try:
        with urllib.request.urlopen(istek, timeout=30) as yanit:
            return yanit.status, yanit.read()
    except urllib.error.HTTPError as hata:
        return hata.code, hata.read()
    except (urllib.error.URLError, TimeoutError, OSError) as hata:
        raise SheetsHatasi(f"Google'a bağlanılamadı. İnternet bağlantınızı kontrol edin. ({hata})") from None


def tablo_kimligi(adres: str) -> str:
    """Tablo adresinden ya da doğrudan kimlikten tablo kimliğini çıkarır."""
    adres = (adres or "").strip()
    m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]{20,})", adres)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{20,}", adres):
        return adres
    raise SheetsHatasi("Tablo adresi anlaşılamadı. Google Sheets tablonuzun tarayıcıdaki adresini yapıştırın "
                       "(https://docs.google.com/spreadsheets/d/... ile başlar).")


# ---------------------------------------------------------------- sayfa → API istekleri

def _renk(onaltilik: str) -> dict:
    return {"red": int(onaltilik[0:2], 16) / 255, "green": int(onaltilik[2:4], 16) / 255, "blue": int(onaltilik[4:6], 16) / 255}


_TL = {"type": "NUMBER", "pattern": '#,##0.00" TL"'}
_YUZDE = {"type": "PERCENT", "pattern": "0.0#%"}
_SARI, _MAVI_YAZI, _LACIVERT, _ACIK_MAVI, _GRI = _renk("FFF2CC"), _renk("0000FF"), _renk("1F3864"), _renk("DDEBF7"), _renk("595959")


def _yazi(**ozellik) -> dict:
    return {"fontFamily": "Arial", "fontSize": 10, **ozellik}


BICEMLER = {
    DUZ: {"textFormat": _yazi(), "verticalAlignment": "TOP"},
    BASLIK: {"textFormat": _yazi(bold=True, fontSize=14)},
    SUTUN: {"textFormat": _yazi(bold=True, foregroundColor=_renk("FFFFFF")), "backgroundColor": _LACIVERT,
            "wrapStrategy": "WRAP", "verticalAlignment": "MIDDLE"},
    ETIKET: {"verticalAlignment": "MIDDLE", "textFormat": _yazi(bold=True)},
    GIRDI_TL: {"verticalAlignment": "MIDDLE", "textFormat": _yazi(foregroundColor=_MAVI_YAZI), "backgroundColor": _SARI, "numberFormat": _TL},
    TL: {"verticalAlignment": "MIDDLE", "textFormat": _yazi(), "numberFormat": _TL},
    GIRDI_YUZDE: {"verticalAlignment": "MIDDLE", "textFormat": _yazi(foregroundColor=_MAVI_YAZI), "backgroundColor": _SARI, "numberFormat": _YUZDE},
    YUZDE: {"verticalAlignment": "MIDDLE", "textFormat": _yazi(), "numberFormat": _YUZDE},
    TAM: {"verticalAlignment": "MIDDLE", "textFormat": _yazi(), "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}},
    NOT: {"textFormat": _yazi(fontSize=9, foregroundColor=_GRI), "wrapStrategy": "WRAP", "verticalAlignment": "TOP"},
    SARMA: {"textFormat": _yazi(), "wrapStrategy": "WRAP", "verticalAlignment": "MIDDLE"},
    ONDALIK: {"verticalAlignment": "MIDDLE", "textFormat": _yazi(), "numberFormat": {"type": "NUMBER", "pattern": "0.0"}},
    VURGU_TL: {"verticalAlignment": "MIDDLE", "textFormat": _yazi(bold=True), "backgroundColor": _ACIK_MAVI, "numberFormat": _TL},
    GIRDI_METIN: {"verticalAlignment": "MIDDLE", "textFormat": _yazi(foregroundColor=_MAVI_YAZI), "backgroundColor": _SARI},
    AFIS: {"textFormat": _yazi(bold=True, fontSize=15, foregroundColor=_renk("FFFFFF")), "backgroundColor": _LACIVERT,
           "verticalAlignment": "MIDDLE", "padding": {"left": 10}},
}


def formul_cevir(ifade: str, ayirici: str) -> str:
    """Formüldeki bağımsız değişken ayırıcısını (tırnak dışındaki virgülleri) değiştirir.

    Ondalık ayırıcısı virgül olan dillerde (Türkçe dahil) Sheets, formülde ';' bekler.
    """
    if ayirici == ",":
        return ifade
    cikti, tirnak = [], None
    for k in ifade:
        if tirnak:
            if k == tirnak:
                tirnak = None
        elif k in ('"', "'"):
            tirnak = k
        elif k == ",":
            k = ayirici
        cikti.append(k)
    return "".join(cikti)


def _hucre(deger, bicem: int, ayirici: str) -> dict:
    hucre: dict = {"userEnteredFormat": BICEMLER.get(bicem, BICEMLER[DUZ])}
    if isinstance(deger, Formul):
        hucre["userEnteredValue"] = {"formulaValue": "=" + formul_cevir(deger.ifade, ayirici)}
    elif isinstance(deger, bool):
        hucre["userEnteredValue"] = {"stringValue": "Evet" if deger else "Hayır"}
    elif isinstance(deger, (int, float)):
        hucre["userEnteredValue"] = {"numberValue": deger}
    elif deger not in (None, ""):
        # stringValue düz metindir: "=" ile başlasa bile formül olarak çalışmaz.
        hucre["userEnteredValue"] = {"stringValue": "".join(k for k in str(deger) if k in "\t\n" or ord(k) >= 32)}
    return hucre


def _aralik(a1: str, sayfa_no: int) -> dict:
    """"A2:K2" → API'nin 0 tabanlı, sonu dahil olmayan aralığı."""
    def coz(h):
        harfler = "".join(k for k in h if k.isalpha())
        sutun = 0
        for k in harfler:
            sutun = sutun * 26 + ord(k) - 64
        return int(h[len(harfler):]), sutun
    (r1, c1), (r2, c2) = (coz(p) for p in a1.split(":"))
    return {"sheetId": sayfa_no, "startRowIndex": r1 - 1, "endRowIndex": r2, "startColumnIndex": c1 - 1, "endColumnIndex": c2}


def sayfa_istekleri(sayfa: Sayfa, sayfa_no: int, ayirici: str) -> list[dict]:
    """Bir sayfanın içeriğini, biçimini ve düzenini yazan istek listesi."""
    son_satir = max(sayfa.satirlar) if sayfa.satirlar else 1
    son_sutun = max(len(sayfa.genislikler), max((s for h in sayfa.satirlar.values() for s, _, _ in h), default=1))
    satirlar = []
    for no in range(1, son_satir + 1):
        hucreler = {s: (d, b) for s, d, b in sayfa.satirlar.get(no, [])}
        satirlar.append({"values": [_hucre(*hucreler[s], ayirici) if s in hucreler else {} for s in range(1, son_sutun + 1)]})
    tum = {"sheetId": sayfa_no}
    istekler: list[dict] = [
        {"unmergeCells": {"range": tum}},
        {"updateCells": {"range": tum, "fields": "userEnteredValue,userEnteredFormat"}},  # önceki içeriği temizler
        {"updateCells": {"start": {"sheetId": sayfa_no, "rowIndex": 0, "columnIndex": 0}, "rows": satirlar,
                         "fields": "userEnteredValue,userEnteredFormat"}},
    ]
    istekler += [{"mergeCells": {"range": _aralik(a, sayfa_no), "mergeType": "MERGE_ALL"}} for a in sayfa.birlesimler]
    for i, genislik in enumerate(sayfa.genislikler):
        istekler.append({"updateDimensionProperties": {
            "range": {"sheetId": sayfa_no, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": int(genislik * 7 + 5)}, "fields": "pixelSize"}})
    for no, yukseklik in sayfa.yukseklikler.items():  # punto → piksel
        istekler.append({"updateDimensionProperties": {
            "range": {"sheetId": sayfa_no, "dimension": "ROWS", "startIndex": no - 1, "endIndex": no},
            "properties": {"pixelSize": int(yukseklik * 4 / 3)}, "fields": "pixelSize"}})
    donuk = int("".join(k for k in sayfa.dondur if k.isdigit())) - 1 if sayfa.dondur else 0
    istekler.append({"updateSheetProperties": {
        "properties": {"sheetId": sayfa_no, "gridProperties": {"frozenRowCount": donuk, "hideGridlines": False}},
        "fields": "gridProperties.frozenRowCount,gridProperties.hideGridlines"}})
    return istekler


SERI_RENKLERI = [_renk("1F3864"), _renk("6FA8DC"), _renk("F6B26B")]


def grafik_istekleri(sayfa: Sayfa, sayfa_no: int) -> list[dict]:
    """Sayfanın grafiklerini ekleyen istekler. Sütun/çubuk grafiği; ilk satır başlık sayılır."""
    istekler = []
    for g in sayfa.grafikler:
        yatay = g["tur"] == "BAR"
        capa = _aralik(f'{g["konum"]}:{g["konum"]}', sayfa_no)
        istekler.append({"addChart": {"chart": {
            "spec": {
                "title": g["baslik"],
                "titleTextFormat": {"fontFamily": "Arial", "fontSize": 13, "bold": True, "foregroundColor": _renk("1F3864")},
                "fontName": "Arial",
                "basicChart": {
                    "chartType": g["tur"], "headerCount": 1,
                    "legendPosition": "BOTTOM_LEGEND" if len(g["seriler"]) > 1 else "NO_LEGEND",
                    "axis": [{"position": "LEFT_AXIS" if yatay else "BOTTOM_AXIS"}, {"position": "BOTTOM_AXIS" if yatay else "LEFT_AXIS"}],
                    "domains": [{"domain": {"sourceRange": {"sources": [_aralik(g["alan"], sayfa_no)]}}}],
                    "series": [{"series": {"sourceRange": {"sources": [_aralik(a, sayfa_no)]}},
                                "targetAxis": "BOTTOM_AXIS" if yatay else "LEFT_AXIS",
                                "colorStyle": {"rgbColor": SERI_RENKLERI[i % len(SERI_RENKLERI)]}}
                               for i, a in enumerate(g["seriler"])],
                },
            },
            "position": {"overlayPosition": {
                "anchorCell": {"sheetId": sayfa_no, "rowIndex": capa["startRowIndex"], "columnIndex": capa["startColumnIndex"]},
                "widthPixels": g["genislik"], "heightPixels": g["yukseklik"]}},
        }}})
    return istekler


# ---------------------------------------------------------------- istemci

class Istemci:
    def __init__(self, anahtar: dict, http=_http):
        self.anahtar, self._http = anahtar, http
        self._jeton, self._bitis = None, 0.0

    @property
    def hesap(self) -> str:
        return self.anahtar["client_email"]

    def _jeton_al(self) -> str:
        if self._jeton and time.time() < self._bitis - 60:
            return self._jeton
        hedef = self.anahtar.get("token_uri") or "https://oauth2.googleapis.com/token"
        govde = ("grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion=" + jwt_olustur(self.anahtar)).encode()
        kod, yanit = self._http("POST", hedef, govde, {"Content-Type": "application/x-www-form-urlencoded"})
        try:
            veri = json.loads(yanit)
        except ValueError:
            veri = {}
        if kod != 200 or "access_token" not in veri:
            raise SheetsHatasi("Google hizmet hesabı anahtarını kabul etmedi. Anahtar silinmiş ya da geçersiz olabilir; "
                               f"Google Cloud'dan yeni bir anahtar indirin. (Ayrıntı: {veri.get('error_description') or veri.get('error') or kod})")
        self._jeton, self._bitis = veri["access_token"], time.time() + int(veri.get("expires_in", 3600))
        return self._jeton

    def _cagir(self, yontem: str, yol: str, govde: dict | None = None) -> dict:
        basliklar = {"Authorization": f"Bearer {self._jeton_al()}", "Content-Type": "application/json"}
        kod, yanit = self._http(yontem, f"{API}/{yol}", json.dumps(govde).encode() if govde is not None else None, basliklar)
        try:
            veri = json.loads(yanit) if yanit else {}
        except ValueError:
            veri = {}
        if kod == 200:
            return veri
        ayrinti = (veri.get("error") or {}).get("message", "")
        if kod == 403 and ("has not been used" in ayrinti or "is disabled" in ayrinti):
            raise SheetsHatasi("Google Cloud projenizde Google Sheets API açık değil. Google Cloud'da “Google Sheets API”yi "
                               "bulup Etkinleştir düğmesine basın, bir iki dakika bekleyip yeniden deneyin.")
        if kod in (403, 404):
            raise SheetsHatasi("Tabloya erişilemedi. Google Sheets tablonuzu açın, Paylaş düğmesine basın ve şu adresi "
                               f"“Düzenleyen” olarak ekleyin: {self.hesap}")
        raise SheetsHatasi(f"Google Sheets isteği başarısız oldu ({kod}). {ayrinti}".strip())

    def yaz(self, tablo: str, sayfalar: list[Sayfa]) -> dict:
        """Verilen sayfaları tabloya yazar. Aynı adlı sekme varsa içeriği değiştirilir; diğer sekmelere dokunulmaz."""
        kimlik = tablo_kimligi(tablo)
        bilgi = self._cagir("GET", f"{kimlik}?fields=properties.locale,sheets.properties.sheetId,sheets.properties.title,"
                                   "sheets.charts.chartId")
        mevcut = {s["properties"]["title"]: s["properties"]["sheetId"] for s in bilgi.get("sheets", [])}
        yazilan = {s.ad for s in sayfalar}
        # Yalnızca bu aracın yazdığı sekmelerdeki eski grafikler silinir; yoksa her çalıştırmada üst üste birikirdi.
        eski_grafikler = [{"deleteEmbeddedObject": {"objectId": c["chartId"]}} for s in bilgi.get("sheets", [])
                          if s["properties"]["title"] in yazilan for c in s.get("charts", [])]
        dil = (bilgi.get("properties") or {}).get("locale", "en_US")
        ayirici = "," if dil.split("_")[0] in ("en", "ja", "zh", "ko", "he", "th", "hi") else ";"

        eksik = [s.ad for s in sayfalar if s.ad not in mevcut]
        if eksik:
            yanit = self._cagir("POST", f"{kimlik}:batchUpdate",
                                {"requests": [{"addSheet": {"properties": {"title": ad}}} for ad in eksik]})
            for cevap in yanit.get("replies", []):
                ozellik = cevap["addSheet"]["properties"]
                mevcut[ozellik["title"]] = ozellik["sheetId"]

        # Yazılan sekmeler en başa alınır: tabloyu açan kişi sonucu ilk sekmede görsün. Başka sekme silinmez.
        one_al = [{"updateSheetProperties": {"properties": {"sheetId": mevcut[s.ad], "index": sira}, "fields": "index"}}
                  for sira, s in enumerate(sayfalar)]

        def gonder(a: str) -> int:
            istekler = [i for s in sayfalar for i in sayfa_istekleri(s, mevcut[s.ad], a)] + one_al
            self._cagir("POST", f"{kimlik}:batchUpdate", {"requests": istekler})
            return self._hata_say(kimlik, [s.ad for s in sayfalar])

        grafikler = [i for s in sayfalar for i in grafik_istekleri(s, mevcut[s.ad])]

        hatali = gonder(ayirici)
        if hatali:  # dil tahmini tutmadıysa diğer ayırıcıyla bir kez daha dene
            diger = "," if ayirici == ";" else ";"
            if gonder(diger) == 0:
                hatali, ayirici = 0, diger
            else:
                hatali = gonder(ayirici)
        if eski_grafikler or grafikler:  # hücreler kesinleştikten sonra, tek seferde
            self._cagir("POST", f"{kimlik}:batchUpdate", {"requests": eski_grafikler + grafikler})
        return {"adres": f"https://docs.google.com/spreadsheets/d/{kimlik}/edit#gid={mevcut[sayfalar[0].ad]}",
                "sekmeler": [s.ad for s in sayfalar], "eklenen_sekmeler": eksik, "hatali_hucre": hatali, "dil": dil,
                "grafik_sayisi": len(grafikler)}

    def _hata_say(self, kimlik: str, adlar: list[str]) -> int:
        """Yazılan sekmelerde hata gösteren (#ERROR!, #NAME? ...) hücre sayısı."""
        from urllib.parse import quote
        araliklar = "&".join("ranges=" + quote("'" + ad.replace("'", "''") + "'") for ad in adlar)
        veri = self._cagir("GET", f"{kimlik}?{araliklar}&fields=sheets.data.rowData.values.effectiveValue.errorValue")
        return sum(1 for s in veri.get("sheets", []) for d in s.get("data", []) for r in d.get("rowData", [])
                   for h in r.get("values", []) if "errorValue" in (h.get("effectiveValue") or {}))


def tabloya_yaz(tablo: str, anahtar_yolu: str | Path, sayfalar: list[Sayfa], http=_http) -> dict:
    return Istemci(anahtar_oku(anahtar_yolu), http).yaz(tablo, sayfalar)


# ---------------------------------------------------------------- kayıtlı bağlantı

KURULMAMIS = "Google Sheets bağlantısı kurulmamış."


def ayar_klasoru() -> Path:
    """Bağlantı ayarları proje klasörünün DIŞINDA, kullanıcının ana klasöründe tutulur."""
    return Path(os.environ.get("PAZAR_KOMISYON_AYAR") or Path.home() / ".pazar-komisyon")


def kayitli_ayar() -> dict:
    try:
        ayar = json.loads((ayar_klasoru() / "ayarlar.json").read_text(encoding="utf-8"))
        return ayar if isinstance(ayar, dict) else {}
    except (OSError, ValueError):
        return {}


def kayitli_istemci(http=_http) -> Istemci:
    try:
        anahtar = json.loads((ayar_klasoru() / "hizmet-hesabi.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise SheetsHatasi(KURULMAMIS) from None
    return Istemci(anahtar, http)


def baglanti_durumu(http=_http) -> dict:
    """Bağlantı kurulu mu? Anahtarın kendisi bu bilgide yer almaz."""
    ayar = kayitli_ayar()
    try:
        hesap = kayitli_istemci(http).hesap
    except SheetsHatasi:
        hesap = None
    return {"ayarli": bool(ayar.get("tablo") and hesap), "hesap": hesap, "tablo": ayar.get("tablo"),
            "tablo_adi": ayar.get("tablo_adi")}


def baglanti_kur(tablo: str, anahtar_icerik: str | None = None, http=_http) -> dict:
    """Anahtarı (verildiyse) saklar, tabloya erişimi dener ve başarılıysa bağlantıyı kaydeder."""
    kimlik = tablo_kimligi(tablo)
    klasor = ayar_klasoru()
    if anahtar_icerik:
        try:
            anahtar = json.loads(anahtar_icerik)
            if not isinstance(anahtar, dict) or anahtar.get("type") != "service_account" or not anahtar.get("client_email"):
                raise ValueError
            rsa_anahtari_coz(str(anahtar.get("private_key") or ""))
        except (ValueError, SheetsHatasi):
            raise SheetsHatasi("Seçtiğiniz dosya bir hizmet hesabı anahtarı değil. Google Cloud'da hizmet hesabı için "
                               "indirdiğiniz JSON dosyasını seçin.") from None
        klasor.mkdir(parents=True, exist_ok=True)
        yol = klasor / "hizmet-hesabi.json"
        yol.write_text(json.dumps(anahtar), encoding="utf-8")
        try:
            yol.chmod(0o600)  # yalnızca bu kullanıcı okuyabilsin
        except OSError:
            pass
    bilgi = kayitli_istemci(http)._cagir("GET", f"{kimlik}?fields=properties.title")
    klasor.mkdir(parents=True, exist_ok=True)
    (klasor / "ayarlar.json").write_text(json.dumps(
        {"tablo": f"https://docs.google.com/spreadsheets/d/{kimlik}/edit", "tablo_adi": (bilgi.get("properties") or {}).get("title") or ""},
        ensure_ascii=False), encoding="utf-8")
    return baglanti_durumu(http)


def baglanti_kaldir() -> None:
    for ad in ("hizmet-hesabi.json", "ayarlar.json"):
        (ayar_klasoru() / ad).unlink(missing_ok=True)


def kayitli_tabloya_yaz(sayfalar: list[Sayfa], http=_http) -> dict:
    tablo = kayitli_ayar().get("tablo")
    if not tablo:
        raise SheetsHatasi(KURULMAMIS)
    return kayitli_istemci(http).yaz(tablo, sayfalar)
