from __future__ import annotations
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

console = Console()


def _db_path(ctx: click.Context) -> Path:
    return Path(ctx.obj["db"])


def _open_db(ctx: click.Context):
    from .database import Database

    db = Database(_db_path(ctx))
    db.connect()
    return db


@click.group()
@click.option(
    "--db",
    default="harmonic_mixer.db",
    show_default=True,
    envvar="HARMONIC_MIXER_DB",
    help="Path to the SQLite database file.",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
@click.pass_context
def cli(ctx: click.Context, db: str, verbose: bool) -> None:
    """Harmonic Mixing Assistant — analyze tracks and find DJ-compatible matches."""
    ctx.ensure_object(dict)
    ctx.obj["db"] = db
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )


@cli.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--workers", default=1, show_default=True, help="Parallel worker processes.")
@click.pass_context
def scan(ctx: click.Context, folder: Path, workers: int) -> None:
    """Scan FOLDER recursively and analyze audio files."""
    from .database import Database
    from .scanner import scan_folder, find_audio_files
    from .analyzer import LibrosaAnalyzer

    db = Database(_db_path(ctx))
    db.connect()

    files = find_audio_files(folder)
    if not files:
        console.print(f"[yellow]No audio files found in {folder}[/yellow]")
        return

    analyzer = LibrosaAnalyzer()

    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning…", total=len(files))
        analyzed_count = 0
        cached_count = 0

        for path in files:
            progress.update(task, description=f"[cyan]{path.name}[/cyan]", advance=1)
            import os
            try:
                stat = path.stat()
            except OSError:
                continue

            mtime, file_size = stat.st_mtime, stat.st_size

            if db.is_cached(str(path), mtime, file_size):
                cached_count += 1
                continue

            from .scanner import _process_file
            row = _process_file(path, mtime, file_size, analyzer)
            if row:
                db.upsert(row)
                analyzed_count += 1

    db.close()
    console.print(
        f"[green]Done.[/green] "
        f"{len(files)} files — "
        f"[blue]{analyzed_count}[/blue] analyzed, "
        f"[dim]{cached_count}[/dim] cached."
    )


@cli.command(name="list")
@click.pass_context
def list_tracks(ctx: click.Context) -> None:
    """Print all analyzed tracks."""
    db = _open_db(ctx)
    rows = db.all_tracks()
    db.close()

    if not rows:
        console.print("[yellow]No tracks in database. Run [bold]scan[/bold] first.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Artist")
    table.add_column("Title")
    table.add_column("BPM", justify="right")
    table.add_column("Key")
    table.add_column("Camelot")
    table.add_column("Source", style="dim")

    for i, r in enumerate(rows, 1):
        table.add_row(
            str(i),
            r.artist or "—",
            r.title or "—",
            f"{r.bpm:.1f}" if r.bpm else "—",
            r.key_name or "—",
            _camelot_badge(r.camelot_key),
            r.tag_source or "—",
        )

    console.print(table)


@cli.command()
@click.argument("track")
@click.option("--bpm-tol", default=0.06, show_default=True, help="BPM tolerance as fraction.")
@click.option("--limit", default=20, show_default=True, help="Max results to display.")
@click.pass_context
def suggest(ctx: click.Context, track: str, bpm_tol: float, limit: int) -> None:
    """Suggest harmonically compatible tracks for TRACK (path or fuzzy title)."""
    from .database import row_to_track_info
    from .matcher import find_matches

    db = _open_db(ctx)

    source_row = db.find_by_path(track)
    if source_row is None:
        matches = db.fuzzy_find(track)
        if not matches:
            console.print(f"[red]Track not found:[/red] {track}")
            db.close()
            sys.exit(1)
        if len(matches) > 1:
            console.print(f"[yellow]Ambiguous match — {len(matches)} results:[/yellow]")
            for m in matches[:5]:
                console.print(f"  {m.path}")
            db.close()
            sys.exit(1)
        source_row = matches[0]

    all_rows = db.all_tracks()
    db.close()

    source_info = row_to_track_info(source_row)
    candidates = [row_to_track_info(r) for r in all_rows]

    if source_info.camelot_key is None:
        console.print("[red]Source track has no key information.[/red]")
        sys.exit(1)

    results = find_matches(source_info, candidates, bpm_tolerance=bpm_tol)

    title_str = f"{source_row.artist or ''} — {source_row.title or source_row.path}"
    console.print(f"\n[bold]Suggestions for:[/bold] {title_str.strip(' —')}")
    console.print(
        f"Key: [bold cyan]{source_row.camelot_key}[/bold cyan]  "
        f"BPM: [bold]{source_row.bpm:.1f}[/bold]\n" if source_row.bpm else ""
    )

    if not results:
        console.print("[yellow]No compatible tracks found.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Score", justify="right", width=6)
    table.add_column("Artist")
    table.add_column("Title")
    table.add_column("BPM", justify="right")
    table.add_column("Camelot")
    table.add_column("ΔBPM", justify="right")

    for m in results[:limit]:
        t = m.track
        table.add_row(
            f"{m.compatibility_score:.2f}",
            t.artist or "—",
            t.title or "—",
            f"{t.bpm:.1f}" if t.bpm else "—",
            _camelot_badge(t.camelot_key),
            f"±{m.bpm_distance:.1f}" if m.bpm_distance else "—",
        )

    console.print(table)


@cli.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show a summary of the analyzed library."""
    db = _open_db(ctx)
    s = db.stats()
    db.close()

    console.print(f"\n[bold]Library stats[/bold]")
    console.print(f"  Total tracks : [bold]{s['total']}[/bold]")
    if s["bpm_min"] is not None:
        console.print(f"  BPM range    : {s['bpm_min']:.1f} – {s['bpm_max']:.1f}")

    if s["key_distribution"]:
        console.print("\n  [bold]Key distribution:[/bold]")
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key")
        table.add_column("Count", justify="right")
        for key, count in list(s["key_distribution"].items())[:24]:
            table.add_row(_camelot_badge(key), str(count))
        console.print(table)


def _camelot_badge(key: str | None) -> str:
    if not key:
        return "—"
    colour = "yellow" if key.endswith("A") else "blue"
    return f"[{colour}]{key}[/{colour}]"
