# Zil — Okul Zil ve Tören Sistemi (v3)

Masaüstü uygulaması + tepsi (system tray) simgesi. Arayüz, Windows 11'in
WebView2 bileşeniyle **kendi uygulama penceresinde** açılır — tarayıcı yok,
adres çubuğu yok. Zil motoru Python tarafında çalışır:
**pencere kapalıyken de ziller çalar.**

Pencereyi kapatmak uygulamadan çıkmaz, tepsiye indirir. Çıkmak için tepsi
menüsünden **Çıkış**.

---

## Çalıştırma

| İşlem | Komut |
|---|---|
| Başlat (tepsiye, pencere gizli) | `pythonw zil.pyw` |
| Başlat + pencereyi aç | `Zil v3.lnk` (masaüstü) veya `pythonw zil.pyw --panel` |
| Pencere yerine tarayıcı kullan | `pythonw zil.pyw --browser` |
| Durum | `python autostart.py status` |
| Açılışta başlat | `python autostart.py enable` |
| Açılıştan kaldır | `python autostart.py disable` |

Tepsi simgesine çift tıklamak paneli açar. Sağ tık menüsü: panel, **tüm sesleri
durdur**, zil sistemini aç/kapat, yapılandırmayı yeniden yükle, çıkış.

## Klasör yapısı

```
Zil/
  zil.pyw          giriş noktası (pythonw = konsol penceresi yok)
  autostart.py     başlangıç / masaüstü kısayolu yönetimi
  core/            motor
    store.py       ayar + program + kayıt dosyaları
    audio.py       öncelikli ses motoru
    scheduler.py   duvar saati zamanlayıcı
    server.py      127.0.0.1 kontrol paneli sunucusu
    app.py         pencere + tepsi + bağlantılar
    window.py      yerel uygulama penceresi (WebView2)
    migrate.py     eski config.js → JSON dönüştürücü
  ui/              kontrol paneli (HTML/CSS/JS)
  audio/           bells/ anthems/ sirens/
  data/            settings.json, schedule.json, ring-log.jsonl,
                   fired-today.json (bugün çalan ziller)
  lib/             gömülü bağımlılıklar (pygame, pystray, Pillow, pywebview)
```

Tüm yapılandırma `data/` içindedir. Klasörü kopyalarsanız sistem taşınır —
tarayıcı `localStorage`'ına bağımlılık yoktur.

---

## Tasarım kararları

**Ses önceliği.** `acil durum (3) > tören (2) > ders zili (1)`. Düşük öncelikli
bir ses, yüksek öncelikli olanı **kesemez**. Yangın sireni çalarken 10:05 çıkış
zili gelirse zil engellenir, siren biter bitmez (tolerans süresi içindeyse) çalar.
**TÜM SESLERİ DURDUR** her zaman önceliklidir.

**Gecikme toleransı.** Ziller tam `HH:MM` eşleşmesiyle değil, geçen süreyle
çalar. Bir kontrol adımı atlanırsa (uyku, yoğunluk) zil `catchup_seconds`
(varsayılan 90 sn) içinde hâlâ çalar. Her zil günde en fazla bir kez çalar.

**%0 gerçekten sessizdir.** v2'de `(değer || 100)` ifadesi 0'ı 100'e çeviriyordu.

**Çift çalma koruması.** Çalan ziller `data/fired-today.json` dosyasına yazılır.
Uygulama bir zilden hemen sonra yeniden başlarsa (çökme, güncelleme, yeniden
başlatma) o zil ikinci kez çalmaz. Gün değişince liste sıfırlanır.

**Güvenlik.** Sunucu yalnızca `127.0.0.1`'e bağlanır ve değişiklik yapan her
istek, sayfaya çalışma anında gömülen oturum anahtarını taşımak zorundadır.
Aksi hâlde tarayıcıdaki herhangi bir sayfa okul zilini çaldırabilirdi.

**Neden .exe değil?** Bu makinede **Smart App Control** etkin (zorunlu kip).
Yeni derlenmiş, imzasız bir `.exe` engellenirdi — nitekim Electron'un yerel
modülü bu yüzden engellendi. Zaten imzalı ve güvenilen `pythonw.exe` üzerinden
çalışmak bu sorunu tamamen ortadan kaldırır.

---

## Zil sesini değiştirme

1. Ses dosyasını doğru klasöre kopyalayın:

   | Ne için | Klasör |
   |---|---|
   | Ders zilleri (öğrenci / öğretmen / çıkış) | `audio\bells\` |
   | Törenler (İstiklal Marşı, saygı duruşu) | `audio\anthems\` |
   | Acil durum sirenleri | `audio\sirens\` |

2. **Ayarlar** sekmesini açın — yeni dosya listede belirir.
3. İlgili zilin açılır listesinden dosyayı seçin, **KAYDET**'e basın.
4. **Panel**'deki manuel düğmeyle dinleyin.

`.wav`, `.mp3` ve `.ogg` desteklenir. Uygulama çalışırken dosya kopyalayabilir,
hatta mevcut bir dosyanın üzerine yazabilirsiniz — çalma bitince dosya serbest
bırakılır.

Dosya adı yanlışsa zil çalmaz; panelde kırmızı uyarı çıkar ve **Kayıt**
sekmesine `error` olarak düşer.

---

## Özel günler

- **Tatiller** — o tarihte ders zili çalmaz. *Bitiş* sütunu doldurulursa aralık
  olur (tek satırda tüm sömestr/yaz tatili). *Yarım gün* saati girilirse o saate
  kadar ziller normal çalar, sonrasında susar — arefe günleri için.
  Aralıklar çakışırsa tam tatil yarım günü ezer.
- **Gün değişimi** — belirli bir tarihte başka bir günün programı uygulanır.
- **Planlı törenler** — tarih + saat + ses. **Tatillerde de çalar** (29 Ekim'de
  zil çalmasın ama İstiklal Marşı çalsın senaryosu için).

---

## Yüklü takvim (2026-2027)

MEB çalışma takvimi ve resmî tatiller **Özel Günler** sekmesinde hazır:

| Tarih | |
|---|---|
| 28.10.2026 | Cumhuriyet Bayramı Arifesi — **yarım gün**, 13:00 sonrası zil yok |
| 29.10.2026 | Cumhuriyet Bayramı |
| 16–20.11.2026 | 1. Dönem Ara Tatili |
| 01.01.2027 | Yılbaşı |
| 25.01–05.02.2027 | Yarıyıl (Sömestr) Tatili |
| 08–12.03.2027 | 2. Dönem Ara Tatili *(Ramazan Bayramı'nı da kapsar)* |
| 23.04.2027 | Ulusal Egemenlik ve Çocuk Bayramı |
| 01.05.2027 | Emek ve Dayanışma Günü |
| 15.05.2027 | Kurban Bayramı Arifesi — **yarım gün**, 13:00 sonrası zil yok |
| 16–19.05.2027 | Kurban Bayramı (19 Mayıs aynı zamanda Gençlik ve Spor Bayramı) |
| 26.06–31.08.2027 | Yaz Tatili |

> **Eylül 2027 kasıtlı olarak boş bırakıldı.** Yaz tatili 31 Ağustos'ta bitiyor;
> 2027-2028 takvimi açıklandığında *Bitiş* tarihini okulun açılış gününe kadar
> uzatın. O güne kadar Eylül 2027'de zil çalar.

Öğretim yılı 14.09.2026 – 25.06.2027. Bu takvimle yıl boyunca **5.074 zil** çalıyor.

---

## Sorun giderme

| Belirti | Bakılacak yer |
|---|---|
| Hiç zil çalmıyor | Panelde durum rozeti *DURAKLATILDI* mı? |
| Ses gelmiyor | Ayarlar → Ses Seviyesi %0 olabilir |
| Panel açılmıyor | Tepsi simgesi duruyor mu? Port 8765 meşgulse 8766+ denenir |
| Ne zaman çaldığını görmek | **Kayıt** sekmesi (`data/ring-log.jsonl`) |
| Ses aygıtı hatası | Panelde kırmızı uyarı şeridi çıkar |


---

## İşletme notları (Ogün'ün kararları ve 21.09.2026 denetiminin bulguları)

Bu bölüm, önceden yalnızca Claude'un hafızasında duran bilgileri herkesin okuyabileceği yere taşır.

- **Bu sistem gerçek okul zillerini çalar.** Yanlış saatte, iki kez veya hiç çalmayan zilin fiziksel sonuçları vardır; **acil durum sirenleri (yangın tahliyesi, sivil savunma) ders zili tarafından asla kesilmemeli.** Ses önceliği: acil durum > tören > zil.
- Başlatmadan veya yeniden başlatmadan önce `data/settings.json` içindeki `enabled` değerine bak. Okul saatinde test etme: gerçekten çalar.
- **Güvenlik açısından kritik parçalar:** `data/fired-today.json` (çift zil koruması), ses öncelik sırası, `catchup_seconds` penceresi. Bunlara dokunursan zamanlayıcı testlerini yeniden çalıştır.
- **Asıl zayıf nokta kod değil, bilgisayarın açık olması:** PC ~08:20'de açılıyor (ilk zil 08:25); Windows Update yeniden başlatması ve ani elektrik kesintileri zilleri kaçırdı (16.09 17:00, 18.09 12:45–13:30). Kaçırılan zil sessizce işaretlenir, günlüğe yazılmaz. **21.09.2026'da Ogün** Windows Update etkin saatlerini 08:00–20:00 yaptı, "Get me up to date"i kapattı, güncelleme sonrası otomatik oturum açmayı (ARSO) açtı; ayrıca grup ilkeleri uygulandı (AUOptions=4, Salı 03:00; NoAutoRebootWithLoggedOnUsers=1). Güncellemeler birikince 17:00'den sonra elle yeniden başlatıyor.
- **Oran duygusu (Ogün'ün kararı):** bazı günlerde 1–2 zilin kaçması kabul edilebilir. BIOS AC-recovery, otomatik oturum açma, UPS ve Wake-on-LAN önerilerini reddetti; günlük boşlukları, DNS-rebinding sertleştirmesini, haftalık marşın otomasyonunu da önemsiz buluyor. **Bunları yeniden gündeme getirme.** Kodun doğruluğu (çift zil, sirenin kesilmesi) yine önemlidir.
- **Cumartesi:** DYK (Pzt–Çar 8.–9. ders ve Cumartesi dersleri) 21.09.2026'da başladı; bilgisayar Cumartesi günleri de açık olmalı.
- **Zil sesleri (21.09.2026'dan beri):** `audio/bells` içinde `Ogrenci_Zili.wav`, `Ogretmen_Zili.wav`, `Cikis_Zili.wav` (Ogün'ün kendi kayıtları, olabildiğince yüksek; Windows ana ses %100). Çalan dosya kilitlidir: dosyayı yerinde değiştirirken Zil boşta olmalı.
- **Haftalık İstiklal Marşı** (Pzt ~08:22, Cuma ~15:23) elle çalınır; `ceremonies` boştur. Eylül 2027'den sonrası bilerek boş bırakıldı.
- **Port 8765:** kontrol paneli `127.0.0.1:8765` dinler. Windows ikinci bir sunucunun aynı porta hata vermeden bağlanmasına izin verir; **test sunucusu için başka bir port kullan** (8792 boştu) ve önce `Get-NetTCPConnection -LocalPort <port> -State Listen` ile bak.
- **Panonun zil saatleri bir kopyadır;** kaynak `data/schedule.json` (her ders için `student`/`teacher`/`exit` satırları). Panoyu güncellerken buradan kopyala, asla hesaplama. **Teneffüsler eşit değildir:** 2. dersten sonra 20 dk (ara öğün, bilerek), diğerleri 15 dk, öğle arası 50 dk. Pano her yerde **öğretmen zilini** kullanır.
- **Neden exe yok:** Smart App Control açık; imzasız yeni `.exe` engellenir. Her şey Python (`pythonw`) üzerinde çalışır.
