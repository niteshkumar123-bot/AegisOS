from datetime import datetime, timedelta, timezone
import hashlib, secrets, base64
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_db
from app.models import User

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password: str) -> str:
    salt=secrets.token_bytes(16)
    digest=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32)
    return "scrypt$16384$"+base64.urlsafe_b64encode(salt).decode()+"$"+base64.urlsafe_b64encode(digest).decode()
def verify_password(password: str, hashed: str) -> bool:
    try:
        scheme,n,salt_s,digest_s=hashed.split("$",3)
        if scheme!="scrypt" or int(n)!=16384: return False
        salt=base64.urlsafe_b64decode(salt_s); expected=base64.urlsafe_b64decode(digest_s)
        actual=hashlib.scrypt(password.encode(),salt=salt,n=int(n),r=8,p=1,dklen=len(expected))
        return secrets.compare_digest(actual,expected)
    except Exception: return False
def create_token(user_id: int) -> str:
    s=get_settings(); now=datetime.now(timezone.utc)
    return jwt.encode({"sub":str(user_id),"iat":now,"exp":now+timedelta(minutes=s.jwt_expire_minutes)}, s.jwt_secret, algorithm="HS256")
def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try:
        payload=jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        uid=int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token", headers={"WWW-Authenticate":"Bearer"})
    user=db.get(User, uid)
    if not user or not user.is_active: raise HTTPException(status_code=401, detail="Invalid or expired access token")
    return user
