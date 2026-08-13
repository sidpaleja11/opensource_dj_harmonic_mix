from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class TrackOut(BaseModel):
    id: int
    path: str
    artist: str | None
    title: str | None
    bpm: float | None
    key_name: str | None
    camelot_key: str | None
    tag_source: str | None
    analyzed_at: str


class MatchOut(BaseModel):
    track: TrackOut
    bpm_distance: float
    compatibility_score: float


class ScanRequest(BaseModel):
    folder: str = Field(..., min_length=1, max_length=1024)

    @field_validator("folder")
    @classmethod
    def folder_must_exist(cls, v: str) -> str:
        resolved = Path(v).resolve()
        if not resolved.exists():
            raise ValueError(f"path does not exist: {v}")
        if not resolved.is_dir():
            raise ValueError(f"path is not a directory: {v}")
        return str(resolved)


class ScanStatusOut(BaseModel):
    status: str
    message: str | None = None


class StatsOut(BaseModel):
    total: int
    bpm_min: float | None
    bpm_max: float | None
    key_distribution: dict[str, int]


class PlaylistItemOut(BaseModel):
    position: int
    track: TrackOut
    compatible: bool  # harmonically compatible with the previous track


class ExportRequest(BaseModel):
    track_ids: list[int] = Field(..., min_length=1)
    name: str | None = Field(None, max_length=200)
