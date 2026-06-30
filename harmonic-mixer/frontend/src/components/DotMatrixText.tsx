import './DotMatrixText.css'

// 5x7 dot-matrix glyphs, '1' = lit dot. Only covers what HARMONIZER needs.
const GLYPHS: Record<string, string[]> = {
  H: ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
  A: ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
  R: ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
  M: ['10001', '11011', '10101', '10101', '10001', '10001', '10001'],
  O: ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
  N: ['10001', '11001', '10101', '10101', '10011', '10001', '10001'],
  I: ['11111', '00100', '00100', '00100', '00100', '00100', '11111'],
  Z: ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
  E: ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
}

export function DotMatrixText({ text }: { text: string }) {
  return (
    <div className="dot-matrix-text">
      {text.split('').map((ch, i) => {
        const pattern = GLYPHS[ch]
        if (!pattern) return null
        return (
          <div className="dot-matrix-letter" key={`${ch}-${i}`}>
            {pattern.map((row, r) => (
              <div className="dot-matrix-row" key={r}>
                {row.split('').map((bit, c) => (
                  <div
                    key={c}
                    className={`dot-matrix-dot${bit === '1' ? ' lit' : ''}`}
                  />
                ))}
              </div>
            ))}
          </div>
        )
      })}
    </div>
  )
}
