import os
import html
import re
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import engine, Base, get_db
from app.cache import cache
import app.models as models
import app.schemas as schemas
from contextlib import asynccontextmanager
import logging
import app.auth as auth

logger = logging.getLogger("cop31.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken veritabanı tablolarını senkronize et
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Veritabanı tabloları senkronize edildi.")
    except Exception as e:
        logger.warning(f"Veritabanı bağlantısı henüz hazır değil: {e}")
    yield

# İstek sınırlayıcı (Rate Limiter) yapılandırması
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(
    title="COP31 Harita Tabanlı Turizm ve Etkinlik Platformu API",
    description="IDD ORG - BM COP31 Antalya Zirvesi için interaktif harita, mekan ve moderasyon servisi",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Beklenmeyen sunucu hatalarında stack trace sızıntısını engelleyen global yakalayıcı (Madde 17)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Beklenmeyen sunucu hatası: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Sunucu tarafında beklenmeyen bir hata oluştu. Güvenlik gereği detaylar gizlenmiştir."}
    )

# CORS Yapılandırması (Madde 12 - Whitelist)
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
else:
    # Geliştirme ve canlı GitHub Pages adresleri
    origins = [
        "http://localhost:3000",
        "http://localhost:5500",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        "https://oku-20237170289.github.io"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# --- İÇERİK FİLTRELEME & GÜVENLİK YARDIMCILARI ---

def sanitize_input(text: Optional[str]) -> str:
    """HTML etiketlerini temizler ve XSS saldırılarına karşı karakterleri zararsız hale getirir (Madde 8)."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]*?>", "", text)
    return html.escape(clean).strip()

BLOCK_WORDS = ["idiot", "hate", "kill", "aptal", "salak"]
FLAG_WORDS = ["scam", "fake", "stupid", "dolandırıcı"]

def detect_language(text: str) -> str:
    """Türkçe karakterleri tarayarak dil tespiti yapar."""
    return "tr" if re.search(r"[çğıöşüÇĞİÖŞÜ]", text) else "en"

def screen_content(text: str):
    """
    Not metnini moderasyon kurallarına göre inceler:
    - İletişim bilgisi veya şüpheli ifadeler varsa bayraklar (flag).
    - Küfür / nefret söylemi varsa engeller (block).
    """
    lower = text.lower()
    
    # 1. E-posta veya telefon numarası tespiti
    if re.search(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", text) or re.search(r"\+?\d[\d\s-]{8,}", text):
        return {"action": "flag", "reason": "screen_contact"}
        
    # 2. Engellenen kelimeler (Nefret / Küfür)
    for word in BLOCK_WORDS:
        if word in lower:
            return {"action": "block", "reason": "screen_language"}
            
    # 3. Şüpheli kelimeler
    for word in FLAG_WORDS:
        if word in lower:
            return {"action": "flag", "reason": "screen_wording"}
            
    # 4. Spam / BÜYÜK HARF kontrolü
    if re.search(r"(.)\1{6,}", text) or (len(text) > 20 and text == text.upper()):
        return {"action": "flag", "reason": "screen_spam"}
        
    return {"action": "pass", "reason": ""}


# --- SİSTEM KONTROLÜ & AUTH ---

@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "COP31 Backend aktif", "version": "1.0.0"}


@app.post("/api/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
@limiter.limit("5/minute")
def register(request: Request, user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta ile kayıtlı bir hesap var.")
    
    new_user = models.User(
        name=user_in.name,
        email=user_in.email,
        password=auth.hash_password(user_in.password),
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/api/login", response_model=schemas.Token, tags=["Auth"])
@limiter.limit("5/minute")
def login(request: Request, credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not auth.verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Hatalı e-posta veya şifre")

    token = auth.create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/api/me", response_model=schemas.UserResponse, tags=["Auth"])
def get_current_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    """Oturum açmış olan kullanıcının bilgilerini döner."""
    return current_user


# --- MEKAN (PLACE) UÇ NOKTALARI (Önbellek & Rate Limit Destekli) ---

@app.get("/api/places", response_model=List[schemas.PlaceResponse], tags=["Places"])
@limiter.limit("120/minute")
def get_places(
    request: Request,
    layer: Optional[str] = Query(None, description="cop31 veya tourism"),
    eco: Optional[bool] = Query(None, description="Sadece sürdürülebilir/eko mekanlar"),
    search: Optional[str] = Query(None, description="İsim veya açıklamada arama"),
    db: Session = Depends(get_db)
):
    # 1. Önbellek kontrolü (Cache Check)
    cache_key = f"places:layer={layer}:eco={eco}:search={search}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # 2. Veritabanı sorgusu
    query = db.query(models.Place)
    if layer:
        query = query.filter(models.Place.layer == layer)
    if eco is not None:
        query = query.filter(models.Place.eco == eco)
    if search:
        query = query.filter(models.Place.name.ilike(f"%{search}%"))
    
    places = query.all()
    encoded_places = jsonable_encoder(places)
    
    # 60 saniye önbelleğe al
    cache.set(cache_key, encoded_places, ttl_seconds=60)
    return encoded_places


@app.get("/api/places/{place_id}", response_model=schemas.PlaceResponse, tags=["Places"])
def get_place(place_id: str, db: Session = Depends(get_db)):
    place = db.query(models.Place).filter(models.Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Mekan bulunamadı")
    return place


@app.post("/api/places", response_model=schemas.PlaceResponse, status_code=status.HTTP_201_CREATED, tags=["Places"])
def create_place(
    place_in: schemas.PlaceCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin)
):
    place_dict = place_in.model_dump(exclude_unset=True)
    if not place_dict.get("id"):
        place_dict.pop("id", None)
    if "name" in place_dict and place_dict["name"]:
        place_dict["name"] = sanitize_input(place_dict["name"])
    if "info" in place_dict and place_dict["info"]:
        place_dict["info"] = sanitize_input(place_dict["info"])

    new_place = models.Place(**place_dict)
    db.add(new_place)
    db.commit()
    db.refresh(new_place)

    # Mekan listesi değiştiğinde önbelleği temizle
    cache.clear_prefix("places:")
    return new_place


@app.put("/api/places/{place_id}", response_model=schemas.PlaceResponse, tags=["Places"])
def update_place(
    place_id: str,
    place_update: schemas.PlaceUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin)
):
    place = db.query(models.Place).filter(models.Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Mekan bulunamadı")

    update_data = place_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ["name", "info", "type"] and isinstance(value, str):
            value = sanitize_input(value)
        setattr(place, field, value)

    db.commit()
    db.refresh(place)

    # Mekan güncellendiğinde önbelleği temizle
    cache.clear_prefix("places:")
    return place


@app.delete("/api/places/{place_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Places"])
def delete_place(
    place_id: str,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin)
):
    place = db.query(models.Place).filter(models.Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Mekan bulunamadı")
    db.delete(place)
    db.commit()

    # Mekan silindiğinde önbelleği temizle
    cache.clear_prefix("places:")
    return None


# --- NOT & MODERASYON UÇ NOKTALARI (Spam Limiti & Önbellek) ---

@app.post("/api/notes", response_model=schemas.NoteResponse, status_code=status.HTTP_201_CREATED, tags=["Notes"])
@limiter.limit("10/minute")
def create_note(
    request: Request,
    note_in: schemas.NoteCreate,
    db: Session = Depends(get_db),
    optional_user: Optional[models.User] = Depends(auth.get_optional_user)
):
    # Mekanın varlığını doğrula
    place = db.query(models.Place).filter(models.Place.id == note_in.place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Mekan bulunamadı")

    # Girdi temizleme (XSS Koruması - Madde 8)
    clean_text = sanitize_input(note_in.text)
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçerli bir not metni giriniz."
        )

    # Otomatik içerik denetimi
    screen_result = screen_content(clean_text)
    if screen_result["action"] == "block":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notunuz uygunsuz ifadeler içerdiği için gönderilemedi."
        )

    # Yazar ismi
    author_name = sanitize_input(note_in.author)
    if not author_name:
        author_name = optional_user.name if optional_user else "Delegate"

    # Dil tespiti
    detected_lang = note_in.lang or detect_language(clean_text)

    # Not oluştur
    new_note = models.Note(
        place_id=note_in.place_id,
        text=clean_text,
        rating=note_in.rating,
        visibility=note_in.visibility or "public",
        status="pending",
        flag_reason=screen_result["reason"] if screen_result["action"] == "flag" else "",
        author=author_name,
        lang=detected_lang
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    # Yeni not geldiğinde önbelleği temizle
    cache.clear_prefix("notes:")
    return new_note


@app.get("/api/notes", response_model=List[schemas.NoteResponse], tags=["Notes"])
@limiter.limit("120/minute")
def get_notes(
    request: Request,
    place_id: Optional[str] = Query(None, description="Mekan ID"),
    status_filter: Optional[str] = Query("approved", description="'approved', 'pending', 'rejected' veya 'all'"),
    db: Session = Depends(get_db)
):
    cache_key = f"notes:place={place_id}:status={status_filter}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    query = db.query(models.Note)
    if place_id:
        query = query.filter(models.Note.place_id == place_id)
    if status_filter and status_filter.lower() != "all":
        query = query.filter(models.Note.status == status_filter.lower())
    
    notes = query.order_by(models.Note.created_at.desc()).all()
    encoded_notes = jsonable_encoder(notes)

    # 30 saniye önbelleğe al
    cache.set(cache_key, encoded_notes, ttl_seconds=30)
    return encoded_notes


@app.patch("/api/notes/{note_id}", response_model=schemas.NoteResponse, tags=["Notes"])
def update_note_status(
    note_id: str,
    status_in: schemas.NoteStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin)
):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Not bulunamadı")

    valid_statuses = ["approved", "rejected", "pending"]
    if status_in.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz durum. Geçerli durumlar: {', '.join(valid_statuses)}"
        )

    note.status = status_in.status
    if status_in.flag_reason is not None:
        note.flag_reason = status_in.flag_reason

    db.commit()
    db.refresh(note)

    # Not onaylandığında veya reddedildiğinde önbelleği temizle
    cache.clear_prefix("notes:")
    return note


@app.delete("/api/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Notes"])
def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(auth.get_current_admin)
):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Not bulunamadı")
    db.delete(note)
    db.commit()

    # Not silindiğinde önbelleği temizle
    cache.clear_prefix("notes:")
    return None


# --- BAŞLANGIÇ VERİLERİNİ YÜKLEME (SEED DATA) ---

@app.post("/api/seed", tags=["Seed"])
def seed_database(db: Session = Depends(get_db)):
    """COP31 için başlangıç mekanları ve hesapları veritabanına ekler."""
    
    # 1. Varsayılan Hesaplar
    default_users = [
        {"email": "admin@cop31.org", "password": auth.hash_password("admin123"), "name": "Moderator", "role": "admin"},
        {"email": "user@cop31.org", "password": auth.hash_password("user123"), "name": "Delegate", "role": "user"},
        {"email": "press@cop31.org", "password": auth.hash_password("press123"), "name": "Press Badge", "role": "user"}
    ]
    added_users = 0
    for u in default_users:
        if not db.query(models.User).filter(models.User.email == u["email"]).first():
            db.add(models.User(**u))
            added_users += 1

    # 2. Başlangıç Mekanları
    seed_places = [
        {"id": "p_expo", "name": "Antalya Expo Center", "type": "COP31 venue", "layer": "cop31", "info": "Main venue. Plenary sessions and daily briefings.", "lat": 36.9402, "lng": 30.8164, "eco": True},
        {"id": "p_hallb", "name": "Side Event Venue", "type": "COP31 venue", "layer": "cop31", "info": "Side events and NGO pavilions.", "lat": 36.9418, "lng": 30.8188, "eco": True},
        {"id": "p_press", "name": "Press Briefing Room", "type": "COP31 venue", "layer": "cop31", "info": "Accreditation desk and press briefing room.", "lat": 36.9389, "lng": 30.8145, "eco": False},
        {"id": "p_cafe", "name": "Green Leaf Cafe", "type": "Vegan restaurant", "layer": "tourism", "info": "Plant-based menu, ten minutes from the venue.", "lat": 36.9365, "lng": 30.8210, "eco": True},
        {"id": "p_hotel", "name": "Aksu Eco Stay", "type": "Eco-hotel", "layer": "tourism", "info": "Low-energy certified hotel with transit access.", "lat": 36.9440, "lng": 30.8100, "eco": True},
        {"id": "p_museum", "name": "Antalya History Museum", "type": "Museum", "layer": "tourism", "info": "Regional history and culture exhibits.", "lat": 36.9330, "lng": 30.8180, "eco": False},
        {"id": "p_market", "name": "Local Organic Market", "type": "Local business", "layer": "tourism", "info": "Local produce and artisan products.", "lat": 36.9375, "lng": 30.8125, "eco": True}
    ]
    added_places = 0
    for p in seed_places:
        if not db.query(models.Place).filter(models.Place.id == p["id"]).first():
            db.add(models.Place(**p))
            added_places += 1

    db.commit()

    # 3. Örnek Notlar
    sample_notes = [
        {"id": "note_sample1", "place_id": "p_expo", "text": "Expo girişi çok hızlı ve organize olmuş.", "rating": 5, "visibility": "public", "status": "approved", "author": "Delegate", "lang": "tr"},
        {"id": "note_sample2", "place_id": "p_cafe", "text": "Vegan menüsü çok lezzetli, tavsiye ederim.", "rating": 4, "visibility": "public", "status": "approved", "author": "Press Badge", "lang": "tr"}
    ]
    added_notes = 0
    for n in sample_notes:
        if not db.query(models.Note).filter(models.Note.id == n["id"]).first():
            db.add(models.Note(**n))
            added_notes += 1

    db.commit()

    # Önbellekleri sıfırla
    cache.clear_prefix("places:")
    cache.clear_prefix("notes:")

    return {
        "status": "success",
        "message": "Seed işlemi tamamlandı.",
        "added_users": added_users,
        "added_places": added_places,
        "added_notes": added_notes
    }