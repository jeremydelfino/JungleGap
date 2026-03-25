from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from database import get_db
from models.user import User
import os

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
SECRET_KEY = os.getenv("SECRET_KEY")

class RegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm="HS256")

@router.post("/register")
def register(body: RegisterSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(400, "Email déjà utilisé")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(400, "Username déjà pris")
    user = User(
        username=body.username,
        email=body.email,
        password_hash=pwd_context.hash(body.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.id), "username": user.username, "coins": user.coins}

@router.post("/login")
def login(body: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(401, "Identifiants incorrects")
    return {"token": create_token(user.id), "username": user.username, "coins": user.coins}