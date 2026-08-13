import { useEffect, useState } from 'react'
import { browseDir, type BrowseResult } from '../api/client'
import './FolderBrowser.css'

interface Props {
  onSelect: (path: string) => void
  onClose: () => void
}

export function FolderBrowser({ onSelect, onClose }: Props) {
  const [current, setCurrent] = useState<BrowseResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function navigate(path?: string) {
    setLoading(true)
    setError(null)
    try {
      const result = await browseDir(path)
      setCurrent(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to browse')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { navigate() }, [])

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') onClose()
  }

  const pathParts = current?.path.replace(/\\/g, '/').split('/').filter(Boolean) ?? []

  return (
    <div className="fb-overlay" onClick={onClose} onKeyDown={handleKeyDown}>
      <div className="fb-modal" onClick={(e) => e.stopPropagation()}>

        <div className="fb-header">
          <div className="eyebrow">
            <div className="eyebrow-dot" />
            <span className="eyebrow-label eyebrow-label-light">browse folders</span>
          </div>
          <button className="fb-close" onClick={onClose}>✕</button>
        </div>

        {/* breadcrumb */}
        <div className="fb-breadcrumb">
          {current?.drives && (
            <button className="fb-crumb" onClick={() => navigate(current.drives![0])}>
              drives
            </button>
          )}
          {pathParts.map((part, i) => {
            const partPath = pathParts.slice(0, i + 1).join('/')
            const fullPath = current?.path.startsWith('/')
              ? `/${partPath}`
              : partPath.replace('/', ':/')
            return (
              <span key={i} className="fb-crumb-wrap">
                <span className="fb-crumb-sep">/</span>
                <button className="fb-crumb" onClick={() => navigate(fullPath)}>
                  {part}
                </button>
              </span>
            )
          })}
        </div>

        {/* drives row — Windows only */}
        {current?.drives && (
          <div className="fb-drives">
            {current.drives.map((d) => (
              <button key={d} className="fb-drive-btn" onClick={() => navigate(d)}>
                {d}
              </button>
            ))}
          </div>
        )}

        {/* directory list */}
        <div className="fb-list">
          {loading && <p className="fb-status">loading…</p>}
          {error && <p className="fb-status fb-error">{error}</p>}

          {!loading && !error && current?.parent && (
            <button className="fb-dir fb-dir-up" onClick={() => navigate(current.parent!)}>
              ↑ ..
            </button>
          )}

          {!loading && !error && current?.dirs.length === 0 && (
            <p className="fb-status">no subfolders</p>
          )}

          {!loading && !error && current?.dirs.map((dir) => (
            <button
              key={dir}
              className="fb-dir"
              onClick={() => navigate(`${current.path}/${dir}`)}
            >
              <span className="fb-dir-icon">▶</span>
              {dir}
            </button>
          ))}
        </div>

        {/* footer */}
        <div className="fb-footer">
          <span className="fb-current-path">{current?.path ?? '…'}</span>
          <button
            className="btn-primary fb-select"
            disabled={!current}
            onClick={() => current && onSelect(current.path)}
          >
            select this folder →
          </button>
        </div>

      </div>
    </div>
  )
}
