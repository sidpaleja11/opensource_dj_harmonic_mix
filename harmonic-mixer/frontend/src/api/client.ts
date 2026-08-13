import type { Match, PlaylistItem, ScanRequest, ScanStatus, ScanProgressEvent, Stats, Track } from '../types'

const BASE = '/api'

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    if (res.status === 502 || res.status === 503 || res.status === 504) {
      throw new Error('API server unreachable — run: python -m harmonic_mixer.cli serve')
    }
    const body = await res.text().catch(() => '')
    let detail: string
    try {
      const parsed = JSON.parse(body) as { detail?: string | Array<{ msg: string }> }
      const d = parsed.detail
      detail = Array.isArray(d) ? d.map((e) => e.msg).join('; ') : (d ?? body)
    } catch {
      detail = body || res.statusText
    }
    throw new Error(`${res.status}: ${detail}`)
  }
  return res.json() as Promise<T>
}

// ── Library ──────────────────────────────────────────────────────────────────

export async function listTracks(params?: {
  q?: string
  key?: string
  bpm_min?: number
  bpm_max?: number
}): Promise<Track[]> {
  const qs = new URLSearchParams()
  if (params?.q)       qs.set('q', params.q)
  if (params?.key)     qs.set('key', params.key)
  if (params?.bpm_min != null) qs.set('bpm_min', String(params.bpm_min))
  if (params?.bpm_max != null) qs.set('bpm_max', String(params.bpm_max))
  const res = await fetch(`${BASE}/tracks/?${qs}`)
  return json<Track[]>(res)
}

export async function getTrack(id: number): Promise<Track> {
  const res = await fetch(`${BASE}/tracks/${id}`)
  return json<Track>(res)
}

// ── Suggest ──────────────────────────────────────────────────────────────────

export async function suggest(
  trackId: number,
  opts?: { bpm_tol?: number; limit?: number },
): Promise<Match[]> {
  const qs = new URLSearchParams()
  if (opts?.bpm_tol != null) qs.set('bpm_tol', String(opts.bpm_tol))
  if (opts?.limit   != null) qs.set('limit',   String(opts.limit))
  const res = await fetch(`${BASE}/suggest/${trackId}?${qs}`)
  return json<Match[]>(res)
}

// ── Scan ─────────────────────────────────────────────────────────────────────

export async function startScan(body: ScanRequest): Promise<ScanStatus> {
  const res = await fetch(`${BASE}/scan/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return json<ScanStatus>(res)
}

/**
 * Opens an SSE connection to /api/scan/progress and calls `onEvent` for each
 * parsed event. Returns a cleanup function that closes the connection.
 */
export function streamScanProgress(
  onEvent: (event: ScanProgressEvent) => void,
  onError?: (err: Event) => void,
): () => void {
  const es = new EventSource(`${BASE}/scan/progress`)
  es.onmessage = (e) => {
    try {
      onEvent(JSON.parse(e.data) as ScanProgressEvent)
    } catch {
      // ignore malformed frames
    }
  }
  if (onError) es.onerror = onError
  return () => es.close()
}

// ── Browse ───────────────────────────────────────────────────────────────────

export interface BrowseResult {
  path: string
  parent: string | null
  dirs: string[]
  drives: string[] | null
}

export async function browseDir(path?: string): Promise<BrowseResult> {
  const qs = path ? `?path=${encodeURIComponent(path)}` : ''
  const res = await fetch(`${BASE}/browse/${qs}`)
  return json<BrowseResult>(res)
}

export async function pickFolder(): Promise<string | null> {
  const res = await fetch(`${BASE}/browse/pick`)
  const data = await json<{ path: string | null }>(res)
  return data.path
}

// ── Playlist ──────────────────────────────────────────────────────────────────

export async function suggestPlaylist(folder: string, bpmTol = 0.06): Promise<PlaylistItem[]> {
  const qs = new URLSearchParams({ folder, bpm_tol: String(bpmTol) })
  const res = await fetch(`${BASE}/playlist/suggest?${qs}`)
  return json<PlaylistItem[]>(res)
}

export async function exportPlaylist(trackIds: number[], name: string): Promise<void> {
  const res = await fetch(`${BASE}/playlist/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ track_ids: trackIds, name }),
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Export failed: ${body || res.statusText}`)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${name}.m3u8`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ── Stats ─────────────────────────────────────────────────────────────────────

export async function getStats(): Promise<Stats> {
  const res = await fetch(`${BASE}/stats`)
  return json<Stats>(res)
}

// ── Health ───────────────────────────────────────────────────────────────────

export async function health(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/health`)
  return json<{ status: string }>(res)
}
