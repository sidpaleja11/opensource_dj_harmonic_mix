import { Link } from 'react-router-dom'
import { DotMatrixText } from '../components/DotMatrixText'
import './LandingPage.css'

const LIBRARY_CARDS = [
  { key: '4A',  bpm: '118 BPM', active: false },
  { key: '6B',  bpm: '122 BPM', active: false },
  { key: '8A',  bpm: '124 BPM', active: true  },
  { key: '9B',  bpm: '126 BPM', active: false },
  { key: '11A', bpm: '128 BPM', active: true  },
  { key: '2A',  bpm: '130 BPM', active: false },
  { key: '3B',  bpm: '132 BPM', active: false },
  { key: '7A',  bpm: '123 BPM', active: false },
  { key: '10B', bpm: '127 BPM', active: false },
  { key: '1A',  bpm: '135 BPM', active: false },
]

export function LandingPage() {
  return (
    <>
      {/* ── NAV ── */}
      <nav className="lp-nav band-white">
        <a href="#" className="lp-logo">HARMONIZER</a>
        <ul className="lp-nav-links">
          <li><a href="#how-it-works">how it works</a></li>
          <li><a href="#the-wheel">the wheel</a></li>
          <li><Link to="/mix">library</Link></li>
          <li><Link to="/scan" className="lp-nav-cta">scan →</Link></li>
        </ul>
      </nav>

      {/* ── WORDMARK ── */}
      <section className="lp-wordmark band-black">
        <DotMatrixText text="HARMONIZER" />
      </section>

      {/* ── HERO ── */}
      <section className="lp-hero band-white">
        <div>
          <div className="eyebrow">
            <div className="eyebrow-dot" />
            <span className="eyebrow-label">harmonic mixing engine</span>
          </div>
          <h1 className="lp-hero-h1">Get your tracks in order.<br />Every time.</h1>
          <p className="lp-hero-sub">
            Harmonzier scans your latest music downloads. It reads the key and tempo of every track,
            then shows you exactly what mixes next. Your folder reorganized before you even open your DJ software.
          </p>
          <div className="lp-hero-ctas">
            <Link to="/scan" className="btn-primary">scan your crate &nbsp;→</Link>
            <a href="#how-it-works" className="btn-ghost">see how it works</a>
          </div>
        </div>

        <div className="lp-vinyl-stage lp-vinyl-overlap">
          <div className="lp-vinyl">
            <div className="lp-vinyl-label">
              <span className="vinyl-brand">HARMONIZER</span>
              <span className="vinyl-side">side a · harmonic mix</span>
              <span className="vinyl-triangle">▶</span>
              <span className="vinyl-key">8A → 9A</span>
              <span className="vinyl-bpm">124 BPM · PERFECT MATCH</span>
              <span className="vinyl-cat">HZ—001</span>
            </div>
            <div className="lp-vinyl-spindle" />
          </div>
        </div>
      </section>

      {/* ── CAMELOT SLIDER ── */}
      <section className="lp-slider band-black" id="the-wheel">
        <div className="eyebrow">
          <div className="eyebrow-dot" />
          <span className="eyebrow-label eyebrow-label-light">compatible next tracks · swipe the wheel</span>
        </div>
        <div className="tracks-row">
          {[
            { key: '6A',  bpm: '82 BPM',  state: 'off-key' },
            { key: '7A',  bpm: '123 BPM', state: 'match'   },
            { key: '8A',  bpm: '124 BPM', state: 'playing' },
            { key: '9A',  bpm: '124 BPM', state: 'match'   },
            { key: '8B',  bpm: '124 BPM', state: 'match'   },
            { key: '5A',  bpm: '126 BPM', state: 'off-key' },
            { key: '10A', bpm: '125 BPM', state: 'off-key' },
            { key: '11A', bpm: '120 BPM', state: 'off-key' },
          ].map((t) => (
            <div key={t.key} className={`track-card ${t.state === 'playing' ? 'playing' : ''} ${t.state === 'off-key' ? 'off-key' : ''}`}>
              <span className="track-key">{t.key}</span>
              <span className="track-bpm">{t.bpm}</span>
              <span className={`track-pill pill-${t.state}`}>{t.state}</span>
            </div>
          ))}
        </div>
        <div className="drag-hint">→ drag</div>
      </section>

      {/* ── DOT MATRIX ── */}
      <section className="lp-dot-matrix band-white">
        <div className="eyebrow">
          <div className="eyebrow-dot" />
          <span className="eyebrow-label">pressed from your library</span>
        </div>
        <div className="dot-grid">
          {LIBRARY_CARDS.map((c) => (
            <div key={c.key} className="dot-card">
              <span className="dot-card-key">{c.key}</span>
              <span className="dot-card-bpm">{c.bpm}</span>
              <div className={`dot-pip${c.active ? ' active' : ''}`} />
            </div>
          ))}
        </div>
        <p className="dot-caption">
          every track analyzed, keyed, and ranked — like a record stamped with its own catalog number.
        </p>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="lp-how band-white" id="how-it-works">
        <div className="eyebrow">
          <div className="eyebrow-dot" />
          <span className="eyebrow-label">how it works</span>
        </div>
        <div className="steps">
          {[
            {
              n: '1', title: 'scan',
              desc: "Drop in a folder. Harmonizer reads every track, pulls existing key and BPM tags, computes what's next.",
            },
            {
              n: '2', title: 'analyze',
              desc: 'Each track lands on the Camelot wheel. Tempo, key, and energy stored locally so re-scans are instant.',
            },
            {
              n: '3', title: 'mix',
              desc: 'Pick a track and see its harmonic neighbors: ranked by key compatibility and BPM, reordering your playlist for you.',
            },
          ].map((s) => (
            <div key={s.n} className="step">
              <div className="tube-numeral">{s.n}</div>
              <h3 className="step-title">{s.title}</h3>
              <p className="step-desc">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── FOOTER CTA ── */}
      <section className="lp-footer band-black" id="download">
        <h2 className="footer-h2">Stop guessing.<br />Start mixing.</h2>
        <div>
          <Link to="/scan" className="footer-btn">scan your crate &nbsp;→</Link>
        </div>
        <span className="footer-tagline">free · open source · mac + windows</span>
      </section>
    </>
  )
}
