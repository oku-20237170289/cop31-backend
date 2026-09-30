import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# .env dosyasını yükle
load_dotenv()

# PostgreSQL bağlantı adresi (.env dosyasından okunur)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError(
        "YAPILANDIRMA HATASI: 'DATABASE_URL' ortam değişkeni tanımlanmamış! "
        "Lütfen .env dosyanızı kontrol edin."
    )

# Veritabanı motorunu oluşturduk
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Veritabanına yapılan her sorgu/işlem için bir oturum - session fabrikası
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Veritabanı modellerimizin miras alacağı temel sınıf
Base = declarative_base()

# FastAPI endpoint'lerinde veritabanı oturumu açıp iş bitince kapatan bağımlılık fonksiyonu
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()