from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_token_payload, purge_expired_tokens
from ..models import RevokedToken, User
from ..ratelimit import login_limiter
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["1. Auth"])


def _token_out(user: User) -> TokenOut:
    token, expires_in = create_access_token(user.id, user.role)
    return TokenOut(access_token=token, expires_in=expires_in, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenOut, status_code=201, summary="Registrasi Learner (FR-01)")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, {"code": "EMAIL_TAKEN", "message": "Email sudah terdaftar."})
    user = User(name=body.name.strip(), email=email, password_hash=hash_password(body.password), role="learner")
    db.add(user)
    db.commit()
    return _token_out(user)


@router.post("/login", response_model=TokenOut, summary="Login & token akses (FR-02)")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    login_limiter.check(f"login:{request.client.host if request.client else 'x'}")
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, {"code": "BAD_CREDENTIALS", "message": "Email atau password salah."})
    from ..services.analytics import record_event
    record_event(db, event_type="login", user_id=user.id, meta={"email": user.email})
    return _token_out(user)


@router.post("/logout", summary="Logout / pembatalan token (FR-03)")
def logout(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)):
    db.merge(RevokedToken(jti=payload["jti"], expires_at=datetime.fromtimestamp(payload["exp"], timezone.utc).replace(tzinfo=None)))
    purge_expired_tokens(db)
    db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserOut, summary="Profil pengguna saat ini")
def me(user: User = Depends(get_current_user)):
    return user
