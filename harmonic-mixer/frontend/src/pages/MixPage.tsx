import { useState } from 'react'
import { Link } from 'react-router-dom'
import { TrackList } from '../components/TrackList'
import { SuggestPanel } from '../components/SuggestPanel'
import type { Track } from '../types'
import './MixPage.css'

export function MixPage() {
  const [selected, setSelected] = useState<Track | null>(null)

  return (
    <div className="mix-root">
      <nav className="lp-nav mix-nav">
        <Link to="/" className="lp-logo">HARMONIZER</Link>
        <ul className="lp-nav-links">
          <li><Link to="/scan">scan</Link></li>
        </ul>
      </nav>

      <div className="mix-layout">
        <aside className="mix-left">
          <TrackList onSelect={setSelected} selectedId={selected?.id ?? null} />
        </aside>

        <main className="mix-right band-black">
          {selected ? (
            <SuggestPanel source={selected} />
          ) : (
            <div className="mix-empty">
              <div className="mix-empty-vinyl lp-vinyl">
                <div className="lp-vinyl-label">
                  <span className="vinyl-brand">HARMONIZER</span>
                  <span className="vinyl-side">side a · your crate</span>
                  <span className="vinyl-triangle">▶</span>
                  <span className="vinyl-key mix-empty-vinyl-key">pick</span>
                  <span className="vinyl-bpm">select a track on the left</span>
                  <span className="vinyl-cat">HZ—MIX</span>
                </div>
                <div className="lp-vinyl-spindle" />
              </div>
              <p className="mix-empty-hint">select a track to see compatible mixes</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
