from __future__ import annotations

import json
from urllib.parse import quote_plus

import anthropic
import httpx
from fastapi import APIRouter, Depends, HTTPException

from harmonic_mixer.camelot import compatible_keys
from harmonic_mixer.database import Database, TrackRow
from ..deps import Settings, get_db, get_settings
from ..schemas import (
    ExternalSuggestOut,
    ExternalSuggestRequest,
    ExternalSuggestion,
    SoundCloudTrack,
)

router = APIRouter(prefix="/api/external", tags=["external"])

_SC_SEARCH = "https://api.soundcloud.com/tracks"
_CLAUDE_MODEL = "claude-sonnet-5"


# ── Prompt ────────────────────────────────────────────────────────────────────

def _compat_set(key: str) -> frozenset[str]:
    return frozenset(compatible_keys(key))


def _build_prompt(tracks: list[TrackRow]) -> str:
    lines: list[str] = []
    for i, t in enumerate(tracks):
        label = f"{t.artist} - {t.title}" if t.artist and t.title else (t.title or t.path.split("\\")[-1].split("/")[-1])
        lines.append(f"{i + 1}. [{t.camelot_key or '?'}] {int(t.bpm or 0)} BPM — {label}")

    transitions: list[str] = []
    gaps: list[str] = []
    for i in range(len(tracks) - 1):
        a, b = tracks[i], tracks[i + 1]
        if a.camelot_key and b.camelot_key and b.camelot_key in _compat_set(a.camelot_key):
            transitions.append(f"  {a.camelot_key} → {b.camelot_key}: compatible")
        else:
            desc = f"  {a.camelot_key or '?'} → {b.camelot_key or '?'}: INCOMPATIBLE"
            transitions.append(desc)
            gaps.append(f"- Between track {i + 1} ({a.camelot_key}) and track {i + 2} ({b.camelot_key})")

    set_block = "\n".join(lines)
    trans_block = "\n".join(transitions) if transitions else "  (no transitions)"
    gaps_block = "\n".join(gaps) if gaps else "  None — set is fully compatible!"

    return f"""You are an expert DJ assistant. Here is a DJ set in harmonic order:

{set_block}

Transition analysis:
{trans_block}

Harmonic gaps (where a bridge track would help):
{gaps_block}

Suggest exactly 3 real, existing tracks that would improve this set by bridging gaps or \
reinforcing strong key clusters. Prioritise electronic/dance music that fits the style of \
the existing tracks.

Return ONLY a valid JSON array — no markdown, no explanation, nothing else:
[
  {{
    "artist": "Exact Artist Name",
    "title": "Exact Track Title",
    "target_camelot_key": "12A",
    "target_bpm": 129,
    "reason": "One sentence: why this bridges the gap or strengthens the set.",
    "search_query": "Artist Name Track Title free download"
  }}
]"""


# ── SoundCloud ────────────────────────────────────────────────────────────────

async def _search_soundcloud(
    http: httpx.AsyncClient,
    query: str,
    client_id: str,
) -> list[SoundCloudTrack]:
    try:
        resp = await http.get(
            _SC_SEARCH,
            params={"client_id": client_id, "q": query, "limit": 4},
        )
        resp.raise_for_status()
        items = resp.json()
    except Exception:
        return []

    results: list[SoundCloudTrack] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        user = item.get("user") or {}
        dl_url: str | None = None
        if item.get("downloadable") and item.get("download_url"):
            dl_url = f"{item['download_url']}?client_id={client_id}"
        art = item.get("artwork_url")
        if art:
            art = art.replace("-large", "-t300x300")
        results.append(SoundCloudTrack(
            sc_id=item.get("id", 0),
            title=item.get("title", ""),
            artist=user.get("username", ""),
            permalink_url=item.get("permalink_url", ""),
            downloadable=bool(item.get("downloadable")),
            download_url=dl_url,
            artwork_url=art,
            bpm=item.get("bpm"),
            genre=item.get("genre"),
        ))
    return results


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/suggest", response_model=ExternalSuggestOut)
async def external_suggest(
    body: ExternalSuggestRequest,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ExternalSuggestOut:
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Set HARMONIC_MIXER_ANTHROPIC_API_KEY in your .env file",
        )

    tracks = [r for tid in body.track_ids if (r := db.find_by_id(tid)) is not None]
    if not tracks:
        raise HTTPException(status_code=404, detail="No tracks found")

    # Call Claude for suggestions
    ai = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        msg = await ai.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=1024,
            system="You are a DJ assistant. Return only valid JSON arrays with no markdown fences.",
            messages=[{"role": "user", "content": _build_prompt(tracks)}],
        )
        raw = msg.content[0].text.strip()
        # Strip markdown fences if the model adds them anyway
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        suggestions_data: list[dict] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"AI returned non-JSON: {exc}") from exc
    except anthropic.APIError as exc:
        raise HTTPException(status_code=502, detail=f"Claude API error: {exc}") from exc

    sc_configured = bool(settings.soundcloud_client_id)
    suggestions: list[ExternalSuggestion] = []

    async with httpx.AsyncClient(timeout=8.0) as http:
        for item in suggestions_data[:3]:
            query: str = item.get("search_query", f"{item.get('artist', '')} {item.get('title', '')}")
            sc_tracks: list[SoundCloudTrack] = []
            if sc_configured:
                sc_tracks = await _search_soundcloud(http, query, settings.soundcloud_client_id)  # type: ignore[arg-type]

            suggestions.append(ExternalSuggestion(
                artist=item.get("artist", ""),
                title=item.get("title", ""),
                target_camelot_key=item.get("target_camelot_key", ""),
                target_bpm=int(item.get("target_bpm", 0)),
                reason=item.get("reason", ""),
                soundcloud_search_url=(
                    f"https://soundcloud.com/search/sounds?q={quote_plus(query)}"
                ),
                soundcloud_tracks=sc_tracks,
            ))

    return ExternalSuggestOut(suggestions=suggestions, soundcloud_configured=sc_configured)
