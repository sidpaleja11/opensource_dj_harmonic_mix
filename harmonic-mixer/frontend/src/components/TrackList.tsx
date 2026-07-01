import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listTracks } from '../api/client'
import type { Track } from '../types'
import './TrackList.css'

interface Props {
  onSelect: (track: Track) => void
  selectedId: number | null
}

export function TrackList({ onSelect, selectedId }: Props) {
  const [tracks, setTracks] = useState<Track[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [q, setQ] = useState('')
  const [bpmMin, setBpmMin] = useState('')
  const [bpmMax, setBpmMax] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listTracks({
        q: q.trim() || undefined,
        bpm_min: bpmMin ? Number(bpmMin) : undefined,
        bpm_max: bpmMax ? Number(bpmMax) : undefined,
      })
      setTracks(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load tracks')
    } finally {
      setLoading(false)
    }
  }, [q, bpmMin, bpmMax])

  useEffect(() => { load() }, [load])

  const filename = (path: string) => path.split(/[\\/]/).pop() ?? path

  return (
    <div className="tl-root">
      <div className="tl-filters">
        <input
          className="tl-search"
          type="search"
          placeholder="search tracks…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <div className="tl-bpm-row">
          <input
            className="tl-bpm-input"
            type="number"
            placeholder="BPM min"
            min={20}
            max={300}
            value={bpmMin}
            onChange={(e) => setBpmMin(e.target.value)}
          />
          <span className="tl-bpm-sep">—</span>
          <input
            className="tl-bpm-input"
            type="number"
            placeholder="max"
            min={20}
            max={300}
            value={bpmMax}
            onChange={(e) => setBpmMax(e.target.value)}
          />
        </div>
      </div>

      <div className="tl-list">
        {loading && <p className="tl-status">loading…</p>}

        {error && <p className="tl-status tl-error">{error}</p>}

        {!loading && !error && tracks.length === 0 && (
          <p className="tl-status">
            no tracks found. <Link to="/scan">scan a folder →</Link>
          </p>
        )}

        {!loading && !error && tracks.map((t) => (
          <button
            key={t.id}
            className={`tl-row${t.id === selectedId ? ' tl-row-active' : ''}`}
            onClick={() => onSelect(t)}
          >
            <span className="tl-row-key">{t.camelot_key ?? '—'}</span>
            <span className="tl-row-info">
              <span className="tl-row-title">{t.title ?? filename(t.path)}</span>
              {t.artist && <span className="tl-row-artist">{t.artist}</span>}
            </span>
            <span className="tl-row-bpm">
              {t.bpm != null ? `${Math.round(t.bpm)} BPM` : '—'}
            </span>
          </button>
        ))}
      </div>

      <div className="tl-footer">
        <span className="tl-count">
          {loading ? '…' : `${tracks.length} track${tracks.length !== 1 ? 's' : ''}`}
        </span>
      </div>
    </div>
  )
}
