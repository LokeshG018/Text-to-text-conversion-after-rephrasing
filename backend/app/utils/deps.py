"""FastAPI dependencies for authentication."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RevokedToken, User
from app.utils.security import decode_token

bearer = HTTPBearer(auto_error=False)


def _resolve(creds: HTTPAuthorizationCredentials | None, db: Session) -> User | None:
    if creds is None:
        return None
    try:
        payload = decode_token(creds.credentials)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if db.get(RevokedToken, payload.get("jti")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has been logged out")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def get_current_user(creds=Depends(bearer), db: Session = Depends(get_db)) -> User:
    user = _resolve(creds, db)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


def get_optional_user(creds=Depends(bearer), db: Session = Depends(get_db)) -> User | None:
    return _resolve(creds, db)
