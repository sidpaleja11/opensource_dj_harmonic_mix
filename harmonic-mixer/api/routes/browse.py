from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/browse", tags=["browse"])


class BrowseOut(BaseModel):
    path: str
    parent: str | None
    dirs: list[str]
    drives: list[str] | None  # Windows only


def _list_dirs(path: Path) -> list[str]:
    try:
        return sorted(
            p.name for p in path.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        )
    except PermissionError:
        return []


def _drives() -> list[str] | None:
    if sys.platform != "win32":
        return None
    import string
    import os
    return [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]


class PickOut(BaseModel):
    path: str | None


def _open_native_dialog() -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        folder = filedialog.askdirectory(parent=root, title="Select music folder")
        root.destroy()
        return folder or None
    except Exception:
        return None


@router.get("/pick", response_model=PickOut)
async def pick_folder() -> PickOut:
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, _open_native_dialog)
    return PickOut(path=path)


@router.get("/", response_model=BrowseOut)
async def browse(
    path: Annotated[str | None, Query(max_length=1024)] = None,
) -> BrowseOut:
    target = Path(path).resolve() if path else Path.home()

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Path does not exist: {target}")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {target}")

    parent = str(target.parent) if target.parent != target else None

    return BrowseOut(
        path=str(target),
        parent=parent,
        dirs=_list_dirs(target),
        drives=_drives(),
    )
