import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import RevokedToken, User, utcnow
from .ratelimit import ai_limiter
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def _unauth(msg: str = "Sesi tidak valid. Silakan login kembali.") -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"code": "UNAUTHORIZED", "message": msg})


def get_token_payload(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> dict:
    if not creds:
        raise _unauth("Token akses diperlukan.")
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise _unauth("Token tidak valid atau sudah kedaluwarsa.") from None
    if db.get(RevokedToken, payload.get("jti")):
        raise _unauth("Token sudah tidak berlaku (logout).")
    return payload


def get_current_user(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)) -> User:
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise _unauth()
    return user


def _require(role: str):
    def checker(user: User = Depends(get_current_user)) -> User:  # FR-04, NFR-09
        if user.role != role:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": f"Endpoint ini khusus role {role}."},
            )
        return user

    return checker


require_learner = _require("learner")
require_admin = _require("admin")


def rate_limit_ai(user: User = Depends(require_learner)) -> User:
    ai_limiter.limit = settings.rate_limit_ai_per_minute
    ai_limiter.check(f"ai:{user.id}")
    return user


def purge_expired_tokens(db: Session) -> None:
    db.query(RevokedToken).filter(RevokedToken.expires_at < utcnow()).delete()
