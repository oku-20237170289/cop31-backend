import uuid
from sqlalchemy import Column, String, Float, Boolean, Integer, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="user")  # "user" veya "admin"


class Place(Base):
    __tablename__ = "places"
    
    id = Column(String, primary_key=True, default=lambda: f"p_{uuid.uuid4().hex[:8]}", index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    layer = Column(String, default="tourism", index=True)  # "cop31" veya "tourism"
    info = Column(Text, nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    eco = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Note(Base):
    __tablename__ = "notes"
    
    id = Column(String, primary_key=True, default=lambda: f"note_{uuid.uuid4().hex[:8]}", index=True)
    place_id = Column(String, ForeignKey("places.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    rating = Column(Integer, default=5)
    visibility = Column(String, default="public")  # "public" veya "limited"
    status = Column(String, default="pending", index=True)     # "pending", "approved", "rejected"
    flag_reason = Column(String, nullable=True, default="")
    author = Column(String, nullable=False)
    lang = Column(String, default="tr")            # "tr" veya "en"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)