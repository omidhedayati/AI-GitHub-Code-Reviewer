import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.config.settings import Settings


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    user_id: uuid.UUID,
    settings: Settings,
    *,
    expires_minutes: int | None = None,
) -> str:
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    expire = datetime.now(UTC) + timedelta(minutes=expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
    }
    return str(
        jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
    )


def create_refresh_token(
    user_id: uuid.UUID,
    settings: Settings,
    *,
    expires_days: int | None = None,
) -> str:
    expire_days = expires_days or settings.refresh_token_expire_days
    expire = datetime.now(UTC) + timedelta(days=expire_days)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }
    return str(
        jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
    )


def decode_token(token: str, settings: Settings) -> dict[str, str]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

    sub = payload.get("sub")
    token_type = payload.get("type")
    if not isinstance(sub, str) or not isinstance(token_type, str):
        raise ValueError("Invalid token payload")

    return {"sub": sub, "type": token_type}
