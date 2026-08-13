import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { exportPlaylist, suggestPlaylist } from '../api/client'
import { ExternalSuggestions } from '../components/ExternalSuggestions'
import type { PlaylistItem } from '../types'
import './PlaylistPage.css'

type Phase = 'idle' | 'loading' | 'before' | 'animating' | 'ready' | 'error'

function camelotCompatible(a: string | null, b: string | null): boolean {
  if (!a || !b) return false
  const num = (s: string) => parseInt(s.slice(0, -1), 10)
  const letter = (s: string) => s.slice(-1)
  const na = num(a), la = letter(a)
  const nb = num(b), lb = letter(b)
  if (na === nb && la === lb) return true
  if (na === nb && la !== lb) return true
  if (la === lb) {
    if ((na % 12) + 1 === nb) return true
    if (((na - 2 + 12) % 12) + 1 === nb) return true
  }
  return false
}

function recomputeCompat(list: PlaylistItem[]): PlaylistItem[] {
  return list.map((item, i) => ({
    ...item,
    position: i + 1,
    compatible: i === 0
      ? false
      : camelotCompatible(list[i - 1].track.camelot_key, item.track.camelot_key),
  }))
}

function trackLabel(item: PlaylistItem): string {
  const t = item.track
  if (t.title) return t.title
  const parts = t.path.replace(/\\/g, '/').split('/')
  return parts[parts.length - 1]
}

function folderName(path: string): string {
  const parts = path.replace(/\\/g, '/').split('/').filter(Boolean)
  return parts[parts.length - 1] ?? 'set'
}

export function PlaylistPage() {
  const [searchParams] = useSearchParams()
  const initialFolder = searchParams.get('folder') ?? ''

  const [folder, setFolder] = useState(initialFolder)
  const [phase, setPhase] = useState<Phase>(initialFolder ? 'loading' : 'idle')
  const [items, setItems] = useState<PlaylistItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)

  const dragIdxRef = useRef<number | null>(null)
  const [dragOver, setDragOver] = useState<number | null>(null)

  // FLIP refs
  const rowRefs = useRef<Map<number, HTMLElement>>(new Map())
  const flipFirstsRef = useRef<Map<number, number> | null>(null)
  const harmonicOrderRef = useRef<PlaylistItem[]>([])

  useEffect(() => {
    if (initialFolder) generate(initialFolder)
  }, [])

  // After React commits the harmonic order to the DOM, apply FLIP transforms
  useLayoutEffect(() => {
    if (!flipFirstsRef.current) return
    const firsts = flipFirstsRef.current
    flipFirstsRef.current = null
    const ordered = harmonicOrderRef.current

    let movers = 0
    ordered.forEach((item, newIdx) => {
      const el = rowRefs.current.get(item.track.id)
      const firstY = firsts.get(item.track.id)
      if (!el || firstY === undefined) return

      const lastY = el.getBoundingClientRect().top
      const dy = firstY - lastY
      if (Math.abs(dy) < 1) return

      movers++
      // Invert: jump element to its old position
      el.style.transition = 'none'
      el.style.transform = `translateY(${dy}px)`

      // Play: animate to final position, staggered by index
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          el.style.transition = `transform 0.55s cubic-bezier(0.4, 0, 0.2, 1) ${newIdx * 28}ms`
          el.style.transform = 'translateY(0)'
        })
      })
    })

    // Clean up inline styles and mark ready after all transitions finish
    const totalDuration = ordered.length * 28 + 600
    setTimeout(() => {
      ordered.forEach(item => {
        const el = rowRefs.current.get(item.track.id)
        if (el) { el.style.transition = ''; el.style.transform = '' }
      })
      setPhase('ready')
    }, totalDuration)
  }, [items])

  async function generate(f = folder) {
    if (!f.trim()) return
    setPhase('loading')
    setError(null)
    rowRefs.current.clear()

    try {
      const harmonic = await suggestPlaylist(f.trim())
      harmonicOrderRef.current = harmonic

      // Build alphabetical "before" order from the same tracks
      const before = [...harmonic]
        .sort((a, b) =>
          (a.track.title ?? trackLabel(a)).localeCompare(b.track.title ?? trackLabel(b))
        )
        .map((item, i) => ({ ...item, position: i + 1, compatible: false }))

      setItems(before)
      setPhase('before')

      // Let user see the "before" state briefly, then trigger FLIP
      await new Promise(res => setTimeout(res, 950))

      // Record current Y positions before React changes the order
      const firsts = new Map<number, number>()
      harmonic.forEach(item => {
        const el = rowRefs.current.get(item.track.id)
        if (el) firsts.set(item.track.id, el.getBoundingClientRect().top)
      })
      flipFirstsRef.current = firsts

      // Switch to harmonic order — useLayoutEffect fires synchronously after DOM update
      setPhase('animating')
      setItems(harmonic)
    } catch (e) {
      setPhase('error')
      setError(e instanceof Error ? e.message : 'Failed to generate playlist')
    }
  }

  function handleDragStart(i: number) { dragIdxRef.current = i }

  function handleDragEnter(i: number) {
    const from = dragIdxRef.current
    if (from === null || from === i) return
    setDragOver(i)
    const next = [...items]
    const [moved] = next.splice(from, 1)
    next.splice(i, 0, moved)
    dragIdxRef.current = i
    setItems(recomputeCompat(next))
  }

  function handleDragEnd() {
    dragIdxRef.current = null
    setDragOver(null)
  }

  async function handleDownload() {
    setDownloading(true)
    try {
      const name = `harmonizer-${folderName(folder)}`
      await exportPlaylist(items.map(it => it.track.id), name)
    } finally {
      setDownloading(false)
    }
  }

  const isAnimating = phase === 'before' || phase === 'animating'
  const showList = phase === 'before' || phase === 'animating' || phase === 'ready'

  return (
    <div className="pl-root">
      <nav className="lp-nav pl-nav band-white">
        <Link to="/" className="lp-logo">HARMONIZER</Link>
        <ul className="lp-nav-links">
          <li><Link to="/scan">scan</Link></li>
          <li><Link to="/mix">library</Link></li>
        </ul>
      </nav>

      <div className="pl-header">
        <div className="eyebrow">
          <div className="eyebrow-dot" />
          <span className="eyebrow-label eyebrow-label-light">set builder</span>
        </div>
        <h1 className="pl-header-title">your set.</h1>
        <div className="pl-folder-row">
          <input
            className="pl-folder-input"
            type="text"
            placeholder="C:\Users\you\Music\DJ Sets"
            value={folder}
            onChange={e => setFolder(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && generate()}
            spellCheck={false}
            autoCorrect="off"
            autoCapitalize="off"
          />
          <button
            className="btn-primary pl-generate-btn"
            onClick={() => generate()}
            disabled={!folder.trim() || phase === 'loading' || isAnimating}
          >
            {phase === 'loading' ? 'fetching…' : isAnimating ? 'sorting…' : 'generate set →'}
          </button>
        </div>
      </div>

      <div className="pl-content">

        {phase === 'idle' && (
          <div className="pl-state">
            <p className="pl-state-text">enter a folder path and hit generate.</p>
          </div>
        )}

        {phase === 'loading' && (
          <div className="pl-state">
            <p className="pl-state-text">reading your crate…</p>
          </div>
        )}

        {phase === 'error' && (
          <div className="pl-state">
            <p className="pl-error-text">{error}</p>
          </div>
        )}

        {showList && (
          <>
            <div className="pl-list-header">
              <div className="pl-list-status">
                {isAnimating ? (
                  <span className="pl-sorting-label">
                    <span className="pl-sorting-dot" />
                    sorting harmonically
                  </span>
                ) : (
                  <span className="pl-list-meta">
                    {items.length} tracks · drag to reorder
                  </span>
                )}
              </div>
              <button
                className="btn-primary pl-download-btn"
                onClick={handleDownload}
                disabled={isAnimating || downloading}
              >
                {downloading ? 'exporting…' : 'download .m3u8 →'}
              </button>
            </div>

            <div className={`pl-list${isAnimating ? ' pl-list-animating' : ''}`}>
              {items.map((item, i) => {
                const keyLetter = item.track.camelot_key?.slice(-1).toLowerCase() ?? 'x'
                const isOver = dragOver === i
                const showCompat = phase === 'ready' && i < items.length - 1

                return (
                  <div
                    key={item.track.id}
                    ref={el => {
                      if (el) rowRefs.current.set(item.track.id, el)
                      else rowRefs.current.delete(item.track.id)
                    }}
                    className={[
                      'pl-row',
                      isAnimating ? 'pl-row-locked' : '',
                      isOver ? 'pl-row-over' : '',
                    ].join(' ').trim()}
                    draggable={phase === 'ready'}
                    onDragStart={() => handleDragStart(i)}
                    onDragEnter={() => handleDragEnter(i)}
                    onDragEnd={handleDragEnd}
                    onDragOver={e => e.preventDefault()}
                  >
                    <span className="pl-handle">{phase === 'ready' ? '≡' : ''}</span>
                    <span className="pl-position">{item.position}</span>
                    <span className={`pl-key pl-key-${keyLetter}`}>
                      {item.track.camelot_key ?? '—'}
                    </span>
                    <div className="pl-meta">
                      <span className="pl-title">{trackLabel(item)}</span>
                      {item.track.artist && (
                        <span className="pl-artist">{item.track.artist}</span>
                      )}
                    </div>
                    <span className="pl-bpm">
                      {item.track.bpm ? Math.round(item.track.bpm) : '—'}
                    </span>
                    {showCompat && (
                      <span className={`pl-compat ${items[i + 1].compatible ? 'pl-compat-ok' : 'pl-compat-bad'}`}>
                        →
                      </span>
                    )}
                    {!showCompat && <span className="pl-compat" />}
                  </div>
                )
              })}
            </div>
          </>
        )}
      </div>
        {phase === 'ready' && items.length > 0 && (
          <ExternalSuggestions trackIds={items.map(it => it.track.id)} />
        )}
    </div>
  )
}
