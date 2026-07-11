from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.db.session import get_db


def get_settings_dep() -> Settings:
    return get_settings()


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


SettingsDep = Depends(get_settings_dep)
DbSessionDep = Depends(get_db_session)
