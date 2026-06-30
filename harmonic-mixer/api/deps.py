from __future__ import annotations

from pathlib import Path
from typing import Generator

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict

from harmonic_mixer.database import Database


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HARMONIC_MIXER_")

    db_path: Path = Path("harmonic_mixer.db")


_settings = Settings()


def get_settings() -> Settings:
    return _settings


def get_db(settings: Settings = Depends(get_settings)) -> Generator[Database, None, None]:
    db = Database(settings.db_path)
    db.connect()
    try:
        yield db
    finally:
        db.close()
