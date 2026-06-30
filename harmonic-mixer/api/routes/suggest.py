from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from harmonic_mixer.database import Database, TrackRow, row_to_track_info
from harmonic_mixer.matcher import find_matches
from ..deps import get_db
from ..schemas import MatchOut, TrackOut

router = APIRouter(prefix="/api/suggest", tags=["suggest"])


def _row_to_out(row: TrackRow) -> TrackOut:
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


@router.get("/{track_id}", response_model=list[MatchOut])
async def suggest(
    track_id: int,
    bpm_tol: Annotated[float, Query(ge=0.01, le=0.5)] = 0.06,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
    db: Database = Depends(get_db),
) -> list[MatchOut]:
    source_row = db.find_by_id(track_id)
    if source_row is None:
        raise HTTPException(status_code=404, detail="Track not found")

    source_info = row_to_track_info(source_row)
    if source_info.camelot_key is None:
        raise HTTPException(status_code=422, detail="Track has no key information")

    all_rows = db.all_tracks()
    path_to_row: dict[str, TrackRow] = {r.path: r for r in all_rows}
    candidates = [row_to_track_info(r) for r in all_rows]

    matches = find_matches(source_info, candidates, bpm_tolerance=bpm_tol)

    results: list[MatchOut] = []
    for m in matches[:limit]:
        row = path_to_row.get(m.track.path)
        if row is None or row.id is None:
            continue
        results.append(
            MatchOut(
                track=_row_to_out(row),
                bpm_distance=m.bpm_distance,
                compatibility_score=m.compatibility_score,
            )
        )

    return results
