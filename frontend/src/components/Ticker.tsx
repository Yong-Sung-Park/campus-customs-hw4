const LINES = [
  'Boola Boola',
  'Bulldog pride, made for New Haven winters',
  '57 Broadway · New Haven',
  'Ask the chat about any size',
  'Hoodies · Crewnecks · Quarter-zips · Fleece',
  'For students, alumni & proud parents',
]

/** Scrolling spirit ticker under the nav (pure CSS animation, duplicated for a seamless loop). */
export default function Ticker() {
  const items = [...LINES, ...LINES]
  return (
    <div className="ticker" aria-hidden="true">
      <div className="ticker-track">
        {items.map((line, i) => (
          <span key={i}>
            {line} <b>✦</b>
          </span>
        ))}
      </div>
    </div>
  )
}
