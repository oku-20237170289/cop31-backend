from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional 
from datetime import datetime

# kullanıcı şemaları

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Şifre en az 8 karakter uzunluğunda olmalıdır.")
        if not any(char.isdigit() for char in v):
            raise ValueError("Şifre en az bir rakam (0-9) içermelidir.")
        if not any(char.isalpha() for char in v):
            raise ValueError("Şifre en az bir harf içermelidir.")
        return v


class UserLogin(BaseModel):

    email: EmailStr
    password: str


class UserResponse(BaseModel):

    id: str
    name: str
    email: EmailStr
    role: str

    class Config:

        from_attributes = True


class Token(BaseModel):

    access_token: str
    token_type: str = "bearer"
    user:UserResponse


# Mekan şemaları

class PlaceBase(BaseModel): 

    name: str
    type: str
    layer: Optional[str] = "tourism"
    info: Optional[str] = ""
    lat: float
    lng: float
    eco: Optional[bool] = False


class PlaceCreate(PlaceBase):
    id: Optional[str] = None


class PlaceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    layer: Optional[str] = None
    info: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    eco: Optional[bool] = None


class PlaceResponse(PlaceBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Not Şemaları

class NoteCreate(BaseModel):
    place_id: str
    text: str
    rating: int = 5
    visibility: Optional[str] = "public"
    author: Optional[str] = None
    lang: Optional[str] = "tr"


class NoteStatusUpdate(BaseModel):

    status: str # -> approved veya rejected
    flag_reason: Optional[str] = ""


class NoteResponse(BaseModel):

    id: str
    place_id: str
    text: str
    rating: int
    visibility: str
    status: str
    flag_reason: Optional[str] = ""
    author: str
    lang: str
    created_at: Optional[datetime] = None

    class Config:

        from_attributes = True