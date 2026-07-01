import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { startScan, streamScanProgress } from '../api/client'
import './ScanPage.css'

type Phase = 'idle' | 'scanning' | 'done' | 'error'

interface DoneStats {
  total: number
  cached: number
  analyzed: number
}

function extractPathFromDrop(e: React.DragEvent): string | null {
  // Chrome/Edge on Windows/Mac passes a file:// URI we can parse into a real path.
  const uriList = e.dataTransfer.getData('text/uri-list')
  if (uriList) {
    const uri = uriList.trim().split('\n')[0].trim()
    if (uri.startsWith('file://')) {
      try {
        // file:///C:/Users/... → C:/Users/... (works for both Win and Mac)
        const decoded = decodeURIComponent(uri.replace(/^file:\/\/\//, ''))
        return decoded || null
      } catch {
        // fall through
      }
    }
  }

  // Fallback: get folder name only from the FileSystemEntry API.
  const entry = e.dataTransfer.items[0]?.webkitGetAsEntry()
  if (entry?.isDirectory) return entry.name

  return null
}

export function ScanPage() {
  const navigate = useNavigate()
  const [folder, setFolder] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [phase, setPhase] = useState<Phase>('idle')
  const [currentFile, setCurrentFile] = useState('')
  const [fileCount, setFileCount] = useState(0)
  const [done, setDone] = useState<DoneStats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const cleanupRef = useRef<(() => void) | null>(null)

  async function handleScan() {
    if (!folder.trim()) return
    setPhase('scanning')
    setCurrentFile('')
    setFileCount(0)
    setError(null)

    try {
      await startScan({ folder: folder.trim() })
    } catch (err) {
      setPhase('error')
      setError(err instanceof Error ? err.message : 'Failed to start scan')
      return
    }

    cleanupRef.current = streamScanProgress(
      (event) => {
        if (event.type === 'progress') {
          setCurrentFile(event.file)
          setFileCount((n) => n + 1)
        } else if (event.type === 'done') {
          cleanupRef.current?.()
          setDone({ total: event.total, cached: event.cached, analyzed: event.analyzed })
          setPhase('done')
        } else if (event.type === 'error') {
          cleanupRef.current?.()
          setPhase('error')
          setError(event.message)
        }
      },
      () => {
        setPhase('error')
        setError('Connection to scan progress lost')
      },
    )
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    setDragOver(true)
  }

  function handleDragLeave(e: React.DragEvent) {
    // only clear if leaving the drop zone entirely
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setDragOver(false)
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragOver(false)
    const path = extractPathFromDrop(e)
    if (path) setFolder(path)
  }

  function handleRetry() {
    cleanupRef.current?.()
    cleanupRef.current = null
    setPhase('idle')
    setError(null)
    setDone(null)
    setFileCount(0)
    setCurrentFile('')
  }

  return (
    <>
      <nav className="lp-nav band-white">
        <Link to="/" className="lp-logo">HARMONIZER</Link>
        <ul className="lp-nav-links">
          <li><Link to="/">home</Link></li>
          <li><Link to="/mix">library</Link></li>
        </ul>
      </nav>

      <main className="scan-page band-black">
        <div className="scan-inner">

          {phase === 'idle' && (
            <>
              <div className="eyebrow">
                <div className="eyebrow-dot" />
                <span className="eyebrow-label eyebrow-label-light">scan your crate</span>
              </div>
              <h1 className="scan-headline">point it at<br />your library.</h1>
              <p className="scan-sub">
                drag a folder in, or paste the path below. harmonizer reads every
                track, extracts key and BPM, and builds your local mix graph.
              </p>

              <div
                className={`scan-dropzone${dragOver ? ' scan-dropzone-active' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className="scan-drop-icon">
                  {dragOver ? '↓' : '⊕'}
                </div>
                <p className="scan-drop-label">
                  {dragOver ? 'drop folder here' : 'drag folder here'}
                </p>
                <p className="scan-drop-hint">or type a path below</p>
              </div>

              <div className="scan-form">
                <input
                  className="scan-input"
                  type="text"
                  placeholder="/Users/you/Music/DJ Sets"
                  value={folder}
                  onChange={(e) => setFolder(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleScan()}
                  spellCheck={false}
                  autoCorrect="off"
                  autoCapitalize="off"
                />
                <button
                  className="btn-primary scan-submit"
                  onClick={handleScan}
                  disabled={!folder.trim()}
                >
                  start scan &nbsp;→
                </button>
              </div>
              <p className="scan-privacy">
                <span className="scan-privacy-red">100% local</span> — your files never leave this machine.
              </p>
            </>
          )}

          {phase === 'scanning' && (
            <>
              <div className="scan-vinyl-wrap">
                <div className="lp-vinyl scan-vinyl-spin">
                  <div className="lp-vinyl-label">
                    <span className="vinyl-brand">HARMONIZER</span>
                    <span className="vinyl-side">scanning · {fileCount} files</span>
                    <span className="vinyl-triangle">▶</span>
                    <span className="vinyl-key scan-vinyl-count">{fileCount}</span>
                    <span className="vinyl-bpm">reading tags + analyzing</span>
                    <span className="vinyl-cat">HZ—SCAN</span>
                  </div>
                  <div className="lp-vinyl-spindle" />
                </div>
              </div>
              <p className="scan-current-file">{currentFile || 'starting…'}</p>
            </>
          )}

          {phase === 'done' && done && (
            <>
              <div className="eyebrow">
                <div className="eyebrow-dot" />
                <span className="eyebrow-label eyebrow-label-light">scan complete</span>
              </div>
              <h2 className="scan-done-head">crate pressed.</h2>
              <div className="scan-stats">
                <div className="scan-stat">
                  <span className="scan-stat-n">{done.total}</span>
                  <span className="scan-stat-label">files found</span>
                </div>
                <div className="scan-stat">
                  <span className="scan-stat-n">{done.analyzed}</span>
                  <span className="scan-stat-label">analyzed</span>
                </div>
                <div className="scan-stat">
                  <span className="scan-stat-n">{done.cached}</span>
                  <span className="scan-stat-label">cached</span>
                </div>
              </div>
              <div className="scan-done-actions">
                <button className="btn-primary scan-submit" onClick={() => navigate('/mix')}>
                  view your library &nbsp;→
                </button>
                <button className="scan-btn-ghost" onClick={handleRetry}>
                  scan another folder
                </button>
              </div>
            </>
          )}

          {phase === 'error' && (
            <>
              <div className="eyebrow">
                <div className="eyebrow-dot" />
                <span className="eyebrow-label eyebrow-label-light">scan failed</span>
              </div>
              <p className="scan-error">{error}</p>
              <button className="scan-btn-ghost" onClick={handleRetry}>try again</button>
            </>
          )}

        </div>
      </main>
    </>
  )
}
