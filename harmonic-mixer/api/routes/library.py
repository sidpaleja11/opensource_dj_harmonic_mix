from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from harmonic_mixer.database import Database, TrackRow
from ..deps import get_db
from ..schemas import TrackOut, StatsOut

router = APIRouter(prefix="/api/tracks", tags=["library"])


def _to_out(row: TrackRow) -> TrackOut:
    assert row.id is not None
    return TrackOut(
        id=row.id,
        path=row.path,
        artist=row.artist,
        title=row.title,
        bpm=row.bpm,
        key_name=row.key_name,
        camelot_key=row.camelot_key,
        tag_source=row.tag_source,
        analyzed_at=row.analyzed_at,
    )


@router.get("/", response_model=list[TrackOut])
async def list_tracks(
    q: Annotated[str | None, Query(max_length=200)] = None,
    key: Annotated[str | None, Query(max_length=10, pattern=r"^\d{1,2}[AB]$")] = None,
    bpm_min: Annotated[float | None, Query(ge=20.0, le=300.0)] = None,
    bpm_max: Annotated[float | None, Query(ge=20.0, le=300.0)] = None,
    db: Database = Depends(get_db),
) -> list[TrackOut]:
    rows = db.fuzzy_find(q) if q else db.all_tracks()

    if key is not None:
        rows = [r for r in rows if r.camelot_key == key]
    if bpm_min is not None:
        rows = [r for r in rows if r.bpm is not None and r.bpm >= bpm_min]
    if bpm_max is not None:
        rows = [r for r in rows if r.bpm is not None and r.bpm <= bpm_max]

    return [_to_out(r) for r in rows]


@router.get("/{track_id}", response_model=TrackOut)
async def get_track(
    track_id: int,
    db: Database = Depends(get_db),
) -> TrackOut:
    row = db.find_by_id(track_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return _to_out(row)
