from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ..deps import Settings, get_settings
from ..schemas import ScanRequest, ScanStatusOut

router = APIRouter(prefix="/api/scan", tags=["scan"])


class _ScanManager:
    """Manages a single background scan and exposes its progress via SSE."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[dict] | None = None

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def has_active_stream(self) -> bool:
        return self._queue is not None

    async def launch(self, folder: Path, db_path: Path) -> None:
        with self._lock:
            if self._running:
                raise RuntimeError("already_running")
            self._running = True
            self._loop = asyncio.get_running_loop()
            self._queue = asyncio.Queue()
        threading.Thread(
            target=self._worker,
            args=(folder, db_path),
            daemon=True,
            name="harmonic-scan",
        ).start()

    def _emit(self, event: dict) -> None:
        if self._loop is not None and self._queue is not None:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

    def _worker(self, folder: Path, db_path: Path) -> None:
        try:
            from harmonic_mixer.database import Database
            from harmonic_mixer.scanner import scan_folder

            with Database(db_path) as db:
                total, cached, analyzed = scan_folder(
                    folder,
                    db,
                    progress=lambda p: self._emit({"type": "progress", "file": str(p)}),
                )
            self._emit(
                {"type": "done", "total": total, "cached": cached, "analyzed": analyzed}
            )
        except Exception as exc:
            self._emit({"type": "error", "message": str(exc)})
        finally:
            with self._lock:
                self._running = False

    async def stream(self) -> AsyncGenerator[str, None]:
        q = self._queue
        if q is None:
            return
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=25.0)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") in ("done", "error"):
                    break
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                with self._lock:
                    if not self._running and q.empty():
                        break


_manager = _ScanManager()


@router.post("/", response_model=ScanStatusOut, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(
    body: ScanRequest,
    settings: Settings = Depends(get_settings),
) -> ScanStatusOut:
    if _manager.running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A scan is already in progress",
        )
    try:
        await _manager.launch(Path(body.folder), settings.db_path)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A scan is already in progress",
        )
    return ScanStatusOut(status="started", message=f"Scanning {body.folder}")


@router.get("/progress")
async def scan_progress() -> StreamingResponse:
    if not _manager.has_active_stream:
        raise HTTPException(status_code=404, detail="No active scan")
    return StreamingResponse(
        _manager.stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
