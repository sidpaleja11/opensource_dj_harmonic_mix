// Mirrors api/schemas.py

export interface Track {
  id: number
  path: string
  artist: string | null
  title: string | null
  bpm: number | null
  key_name: string | null
  camelot_key: string | null
  tag_source: string | null
  analyzed_at: string
}

export interface Match {
  track: Track
  bpm_distance: number
  compatibility_score: number
}

export interface ScanRequest {
  folder: string
}

export interface ScanStatus {
  status: string
  message: string | null
}

export interface Stats {
  total: number
  bpm_min: number | null
  bpm_max: number | null
  key_distribution: Record<string, number>
}

export interface PlaylistItem {
  position: number
  track: Track
  compatible: boolean
}

// SSE event shapes from /api/scan/progress
export type ScanProgressEvent =
  | { type: 'progress'; file: string }
  | { type: 'done'; total: number; cached: number; analyzed: number }
  | { type: 'error'; message: string }
