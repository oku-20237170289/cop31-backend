# 🌍 COP31 Türkiye - Harita Tabanlı Turizm ve Etkinlik Platformu Backend Servisi (Demo 1)

Bu proje, Birleşmiş Milletler nezdinde tanınan küresel gençlik organizasyonu **İklim Değişmeden Değiş (IDD ORG)** teknoloji ekibi tarafından, Türkiye'nin ev sahipliğinde Antalya'da gerçekleşecek olan **COP31 İklim Zirvesi** için geliştirilen harita tabanlı web aplikasyonunun arka yüz (backend) servisidir.

---

## 📌 Proje Vizyonu ve Amacı

COP31 Zirvesi boyunca Antalya'yı ziyaret edecek on binlerce delege, sivil toplum kuruluşu temsilcisi, aktivist ve katılımcı için sürdürülebilirlik odaklı dijital bir rehber sunulmaktadır:
- **Resmi COP31 Operasyon Alanları:** Plenary alanları, brifing salonları, basın odaları ve STK pavyonları.
- **Sürdürülebilir Turizm:** Vegan/vejetaryen restoranlar, eko-oteller, yerel işletmeler ve kültürel miras noktaları.
- **Topluluk Etkileşimi ve Moderasyon:** Ziyaretçilerin haritaya yer işareti (pin) ve not bırakabilmesi, yönetici moderasyon onayı ve otomatik içerik filtrelemesi.

---

## 🛠️ Teknoloji Mimarisi

- **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Veritabanı:** PostgreSQL (Docker Konteyner Altyapısı)
- **ORM / Veri Katmanı:** SQLAlchemy & Pydantic v2
- **Kimlik Doğrulama:** JWT (JSON Web Tokens) & Bcrypt Şifreleme
- **İçerik Güvenliği:** Otomatik küfür/hakaret engelleme (Content Screening) & dil tespiti
- **Hız Sınırlama (Rate Limiting):** SlowAPI ile brute-force ve spam koruması (Login: 5/dk, Notlar: 10/dk)
- **Önbellekleme (Caching):** In-Memory / Redis TTL önbellekleme ve anlık geçersiz kılma (cache invalidation)

---

## 🚀 Temel Özellikler ve API Uç Noktaları

### 1. Kimlik Doğrulama & Yetkilendirme (Auth)
- `POST /api/register` : Yeni kullanıcı kaydı.
- `POST /api/login` : Güvenli giriş ve JWT Bearer token üretimi.
- `GET /api/me` : Oturum açmış kullanıcının profil ve rol bilgisi.

### 2. Mekan Yönetimi (Places)
- `GET /api/places` : Katmana (`cop31` veya `tourism`), eko-sertifikaya (`eco=true`) veya isme göre filtreli mekan listesi.
- `GET /api/places/{id}` : Mekan detayları.
- `POST /api/places` : Yeni mekan ekleme (*Admin yetkili*).
- `PUT /api/places/{id}` : Mekan güncelleme (*Admin yetkili*).
- `DELETE /api/places/{id}` : Mekan silme (*Admin yetkili*).

### 3. Not Bırakma & Moderasyon (Notes)
- `POST /api/notes` : Ziyaretçi notu bırakma. Otomatik spam/iletişim bilgisi bayraklama ve küfür engelleme içerir. Varsayılan olarak onaya (`pending`) düşer.
- `GET /api/notes` : Onaylanmış notları listeleme (`status_filter=approved`).
- `PATCH /api/notes/{id}` : Admin not onaylama (`approved`), reddetme (`rejected`) veya kuyruğa geri çekme (`pending`).
- `DELETE /api/notes/{id}` : Admin not silme.

### 4. Başlangıç Verileri (Seed Data)
- `POST /api/seed` : Antalya Expo Center, Salonlar ve sürdürülebilir kafeleri içeren ilk verileri tek tıkla veritabanına yükler.

---

## 💻 Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.10 veya üzeri
- Docker Desktop (PostgreSQL için)

### 1. Adım: Veritabanını Başlatma
Docker üzerinden PostgreSQL konteynerinizin çalıştığından emin olun (Varsayılan Port: `5434`).

### 2. Adım: Ortam Değişkenleri
`.env.example` dosyasını kopyalayarak `.env` adıyla kaydedin:
```env
DATABASE_URL=postgresql://kullanici_adi:sifre@localhost:5434/cop31_db
SECRET_KEY=buraya_guclu_ve_rastgele_bir_jwt_gizli_anahtari_yaziniz
PORT=8000
```

### 3. Adım: Servisi Başlatma
- **Windows için (En Kolay):** `start.bat` dosyasına çift tıklayın.
- **Terminalden:**
```bash
# Sanal ortamı aktif et
.\venv\Scripts\activate

# Servisi çalıştır
python run.py
```

### 4. Adım: İnteraktif API Dokümantasyonu (Swagger)
Servis başladıktan sonra tarayıcınızdan şu adrese gidin:
👉 **http://127.0.0.1:8000/docs**

---

## 👥 Ekip & İletişim

- **Organizasyon:** [İklim Değişmeden Değiş (IDD ORG)](https://www.iklimdd.org)
- **Birim:** IDD ORG Teknoloji & Yazılım Geliştirme Ekibi
- **Etkinlik:** UN Climate Change Conference COP31 Türkiye / Antalya
