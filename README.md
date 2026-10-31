# WordSpring — İngilizce Kelime Öğrenme

Türkçe arayüzlü, Windows 10 ve Windows 11 için hazırlanmış çevrimdışı İngilizce kelime çalışma uygulaması. Uygulama A2 ve B1 düzeylerinde **500 kelime** içerir: 250 A2 ve 250 B1. Açıklamalar ve örnek cümleler, İngilizceyi bağlam içinde öğrenmeye yardımcı olmak için basit İngilizceyle yazılmıştır.

## Hazır uygulamayı çalıştırma

`dist\WordSpring.exe` dosyasına çift tıklayın. Bilgisayara Python kurmanız gerekmez. İlk açılışta uygulama kelime listesini ve ses önbelleğini Windows kullanıcı klasörüne kaydeder.

## Kaynak koddan çalıştırma

1. 64 bit Python 3.11 veya daha yeni bir sürüm kurun. Windows Python Launcher (`py`) da kurulu olmalıdır.
2. `setup_windows.bat` dosyasına çift tıklayın. Betik, `requirements.lock` içindeki sabitlenmiş sürümleri kurar.
3. Uygulamayı açmak için `run_windows.bat` dosyasına çift tıklayın.

PowerShell ile de çalıştırabilirsiniz:

```powershell
python -m pip install -r requirements.lock
python main.py
```

## Windows `.exe` oluşturma ve kurma

`build_windows.bat` taşınabilir uygulamayı `dist\WordSpring.exe` yolunda oluşturur. Bunu çalıştırmak için Python gerekmez; uygulama kurulmadan açılır.

Normal kurulum paketi için `build_installer.bat` dosyasını çalıştırın. Betik `dist\WordSpring-Setup.exe` üretir. Kurulum uygulamayı geçerli Windows kullanıcısının Programs klasörüne koyar, masaüstü kısayolu ve Başlat menüsü girişleri oluşturur, kaldırıcı ekler ve kurulum sonunda uygulamayı başlatma seçeneği sunar. Kurulum yönetici izni istemez. Kelime ilerlemesi `%LOCALAPPDATA%\WordSpring` içinde kaldığı için uygulamayı kaldırıp daha sonra yeniden kurduğunuzda veriler korunur. Kurulum paketini derlemek için Inno Setup 7 gerekir.

Kullanıcılara önerilen indirme, [GitHub Releases](https://github.com/mikegit-lb/WordSpring) sayfasındaki `WordSpring-Setup.exe` dosyasıdır. `WordSpring.exe` taşınabilir sürüm olarak ayrıca sunulur.

## Microsoft Store paketi

Store için tek dosya yerine daha hızlı açılan onedir derlemesi MSIX içine alınır. `build_store_msix.ps1` Partner Center'daki tam uygulama kimliğiyle `dist\WordSpring-1.0.1.0.msix` dosyasını üretir ve paketi açarak yapısal olarak doğrular. Kimlik alanları Store'da uygulama adını ayırdıktan sonra verilmelidir; rastgele değer kullanmayın. Komut ve listeleme taslakları `store\STORE_SUBMISSION.md` dosyasındadır. Listing görselleri `store\Assets` ve `store\Screenshots` klasörlerindedir.

Store sürümü çevrimdışı SAPI sesini kullanır; isteğe bağlı çevrimiçi TTS bileşenini içermez. Uygulama Qt for Python'ın topluluk sürümünü kullanır. Store'a dağıtım öncesinde `THIRD_PARTY_NOTICES.md` içindeki Qt LGPL koşullarını gözden geçirin; bu koşulları karşılayamıyorsanız uygun Qt ticari lisansı gerekir. Partner Center hesabı, ayrılmış uygulama kimliği, yaş derecelendirme formu, yayıncı iletişim bilgileri ve son Windows App Certification Kit sonucu yayıncı tarafından tamamlanmalıdır.

## Çalışma özellikleri

- Kelime kartları, IPA telaffuzu, sesli okuma, vurgulanmış örnek cümleler ve tekrar derecelendirme
- Değiştirilmiş SM-2 aralıklı tekrar planı: Tekrar, Zor, İyi ve Kolay seçenekleri
- Tanım eşleştirme, B1 cümle tamamlama ve dinleyerek yazma alıştırmaları
- A2/B1 filtresi, aranabilir kelime kütüphanesi ve özel kelime ekleme
- Öğrenilen kelime, bugünkü tekrar, doğruluk oranı ve günlük seri göstergeleri
- Açık ve koyu tema
- Windows SAPI üzerinden çevrimdışı İngilizce seslendirme; oluşturulan sesler yerel olarak saklanır

Windows'ta İngilizce SAPI sesi kurulu ve etkin olmalıdır. SAPI kullanılamazsa seslendirme özelliği hata vermeden devre dışı kalır. İsteğe bağlı `edge-tts` sağlayıcısı, çevrimdışı SAPI yerine çevrimiçi ses kullanır.

## Veriler ve gizlilik

Kelime veritabanı `%LOCALAPPDATA%\WordSpring\vocab.db`, ses dosyaları ise `%LOCALAPPDATA%\WordSpring\audio` klasöründe tutulur. Çalışma geçmişi cihazınızda kalır. Yeni sürümler eksik başlangıç kelimelerini ekler; özel kelimelerinizi ve tekrar geçmişinizi korur.

Uygulama açılırken SQLite veritabanını denetler. Hasarlı bir dosya bulunursa, uygulama bunu `vocab.corrupt-<tarih>.db` adıyla kurtarma kopyası olarak saklamayı dener ve temiz bir veritabanı oluşturur. Veritabanı açılmaz veya kurtarılamazsa uygulama anlaşılır bir hata penceresi gösterir.

## Proje dosyaları

- `main.py` — uygulama başlangıcı ve kullanıcı klasörleri
- `ui_main.py` — Türkçe arayüz, kartlar, alıştırmalar, kelime kütüphanesi ve ilerleme ekranı
- `database.py` — SQLite şeması, güncellemeler, kelimeler ve ilerleme kayıtları
- `srs.py` — aralıklı tekrar hesaplamaları
- `audio.py` — SAPI/isteğe bağlı çevrimiçi seslendirme ve ses önbelleği
- `seed_data.py`, `additional_seed_data.py` — 500 A2/B1 kelimesi
- `requirements.txt` — Python bağımlılıkları
- `THIRD_PARTY_NOTICES.md` — kelime verileri için kaynak ve lisans bilgileri

Kelime seviyesi, Oxford 3000 CEFR listesinden yararlanılarak seçilmiştir. WordSpring, Oxford veya English Profile tarafından yayımlanmış ya da onaylanmış bir ürün değildir. Veri kaynaklarının atıf ve lisans bilgileri `THIRD_PARTY_NOTICES.md` dosyasındadır.
