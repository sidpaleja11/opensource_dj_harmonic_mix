import type { Match, ScanRequest, ScanStatus, ScanProgressEvent, Stats, Track } from '../types'

const BASE = '/api'

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    if (res.status === 502 || res.status === 503 || res.status === 504) {
      throw new Error('API server unreachable — run: python -m harmonic_mixer.cli serve')
    }
    const body = await res.text().catch(() => '')
    let detail: string
    try {
      detail = (JSON.parse(body) as { detail?: string }).detail ?? body
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
