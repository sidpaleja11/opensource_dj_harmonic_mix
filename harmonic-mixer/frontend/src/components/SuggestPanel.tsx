import { useEffect, useState } from 'react'
import { suggest } from '../api/client'
import type { Match, Track } from '../types'
import './SuggestPanel.css'

interface Props {
  source: Track
}

function cardState(m: Match, source: Track): 'playing' | 'match' {
  return m.track.camelot_key === source.camelot_key ? 'playing' : 'match'
}

export function SuggestPanel({ source }: Props) {
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const filename = (path: string) => path.split(/[\\/]/).pop() ?? path

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setMatches([])
    setError(null)

    suggest(source.id)
      .then((data) => { if (!cancelled) setMatches(data) })
      .catch((e) => { if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load suggestions') })
      .finally(() => { if (!cancelled) setLoading(false) })

    return () => { cancelled = true }
  }, [source.id])

  return (
    <div className="sp-root">
      <div className="sp-source">
        <div className="eyebrow">
          <div className="eyebrow-dot" />
          <span className="eyebrow-label eyebrow-label-light">now mixing</span>
        </div>
        <div className="sp-source-info">
          <span className="sp-source-key">{source.camelot_key ?? '—'}</span>
          <span className="sp-source-meta">
            <span className="sp-source-title">{source.title ?? filename(source.path)}</span>
            {source.artist && <span className="sp-source-artist">{source.artist}</span>}
            {source.bpm != null && (
              <span className="sp-source-bpm">{Math.round(source.bpm)} BPM</span>
            )}
          </span>
        </div>
      </div>

      <div className="eyebrow sp-matches-eyebrow">
        <div className="eyebrow-dot" />
        <span className="eyebrow-label eyebrow-label-light">compatible next tracks</span>
      </div>

      {loading && <p className="sp-status">finding matches…</p>}
      {error && <p className="sp-status sp-error">{error}</p>}
      {!loading && !error && matches.length === 0 && (
        <p className="sp-status">no compatible tracks found.</p>
      )}

      {!loading && !error && matches.length > 0 && (
        <div className="tracks-row sp-slider">
          {matches.map((m) => {
            const state = cardState(m, source)
            return (
              <div
                key={m.track.id}
                className={`track-card${state === 'playing' ? ' playing' : ''}`}
              >
                <span className="track-key">{m.track.camelot_key ?? '—'}</span>
                <span className="track-bpm">
                  {m.track.bpm != null ? `${Math.round(m.track.bpm)} BPM` : '—'}
                </span>
                <span className={`track-pill ${state === 'playing' ? 'pill-playing' : 'pill-match'}`}>
                  {state === 'playing' ? 'same key' : 'match'}
                </span>
                <span className="sp-card-title">
                  {m.track.title ?? filename(m.track.path)}
                </span>
                <span className="sp-card-score">
                  {(m.compatibility_score * 100).toFixed(0)}%
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
