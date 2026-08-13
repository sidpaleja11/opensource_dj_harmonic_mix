import { useState } from 'react'
import { fetchExternalSuggestions } from '../api/client'
import type { ExternalSuggestion, ExternalSuggestOut, SoundCloudTrack } from '../types'
import './ExternalSuggestions.css'

interface Props {
  trackIds: number[]
}

type Phase = 'idle' | 'loading' | 'ready' | 'error'

function KeyBadge({ camelot }: { camelot: string }) {
  const letter = camelot.slice(-1).toLowerCase()
  return (
    <span className={`es-key es-key-${letter === 'a' ? 'a' : letter === 'b' ? 'b' : 'x'}`}>
      {camelot}
    </span>
  )
}

function ScTrackRow({ track }: { track: SoundCloudTrack }) {
  return (
    <div className="es-sc-row">
      {track.artwork_url ? (
        <img className="es-sc-art" src={track.artwork_url} alt="" loading="lazy" />
      ) : (
        <div className="es-sc-art es-sc-art-placeholder" />
      )}
      <div className="es-sc-meta">
        <span className="es-sc-title">{track.title}</span>
        <span className="es-sc-artist">{track.artist}</span>
        {track.bpm && <span className="es-sc-bpm">{Math.round(track.bpm)} BPM</span>}
      </div>
      <div className="es-sc-actions">
        {track.downloadable && track.download_url && (
          <a
            className="es-sc-dl"
            href={track.download_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            free ↓
          </a>
        )}
        <a
          className="es-sc-link"
          href={track.permalink_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          soundcloud ↗
        </a>
      </div>
    </div>
  )
}

function SuggestionCard({ s, scConfigured }: { s: ExternalSuggestion; scConfigured: boolean }) {
  return (
    <div className="es-card">
      <div className="es-card-head">
        <KeyBadge camelot={s.target_camelot_key} />
        <span className="es-card-bpm">{s.target_bpm} BPM</span>
        <div className="es-card-title-group">
          <span className="es-card-track">{s.artist} — {s.title}</span>
          <span className="es-card-reason">{s.reason}</span>
        </div>
      </div>

      {s.soundcloud_tracks.length > 0 ? (
        <div className="es-sc-list">
          {s.soundcloud_tracks.map(t => (
            <ScTrackRow key={t.sc_id} track={t} />
          ))}
        </div>
      ) : (
        <div className="es-sc-fallback">
          {scConfigured
            ? 'No SoundCloud results for this query.'
            : 'SoundCloud client ID not configured — '}
          <a
            className="es-sc-link"
            href={s.soundcloud_search_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            search on SoundCloud ↗
          </a>
        </div>
      )}
    </div>
  )
}

export function ExternalSuggestions({ trackIds }: Props) {
  const [phase, setPhase] = useState<Phase>('idle')
  const [result, setResult] = useState<ExternalSuggestOut | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function find() {
    setPhase('loading')
    setError(null)
    try {
      const data = await fetchExternalSuggestions(trackIds)
      setResult(data)
      setPhase('ready')
    } catch (e) {
      setPhase('error')
      setError(e instanceof Error ? e.message : 'Request failed')
    }
  }

  return (
    <div className="es-root">
      <div className="es-header">
        <div className="eyebrow">
          <div className="eyebrow-dot" />
          <span className="eyebrow-label eyebrow-label-light">AI track finder</span>
        </div>
        <p className="es-sub">
          Claude analyses your set's harmonic gaps and suggests real tracks to fill them.
          Results are pulled from SoundCloud — free downloads flagged where available.
        </p>
        {phase !== 'ready' && (
          <button
            className="btn-primary es-find-btn"
            onClick={find}
            disabled={phase === 'loading'}
          >
            {phase === 'loading' ? 'asking claude…' : 'find compatible tracks →'}
          </button>
        )}
        {phase === 'ready' && (
          <button className="es-reset-btn" onClick={() => { setPhase('idle'); setResult(null) }}>
            search again
          </button>
        )}
      </div>

      {phase === 'error' && (
        <p className="es-error">{error}</p>
      )}

      {phase === 'ready' && result && (
        <div className="es-cards">
          {result.suggestions.map((s, i) => (
            <SuggestionCard key={i} s={s} scConfigured={result.soundcloud_configured} />
          ))}
        </div>
      )}
    </div>
  )
}
