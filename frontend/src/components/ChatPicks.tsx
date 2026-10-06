import { useLocation } from 'react-router-dom'
import { useChat } from '../chat.tsx'
import ProductCard from './ProductCard.tsx'

/** Product cards the chat agent found, shown at the top of whatever page the shopper is on. */
export default function ChatPicks() {
  const { picks, picksFor, picksPath, clearPicks } = useChat()
  const { pathname } = useLocation()
  if (picks.length === 0) return null
  // Full grid only on the page where the shopper asked. Anywhere else (including
  // product pages) it shrinks to a one-row strip so the page's own content is visible.
  const compact = pathname !== picksPath || pathname.startsWith('/products/')

  return (
    <section className={`picks${compact ? ' picks-compact' : ''}`} aria-label="Products picked by chat">
      <div className="picks-inner">
        <div className="picks-head">
          <div>
            <p className="eyebrow">Picked for you by chat</p>
            <h2>“{picksFor}”</h2>
          </div>
          <button type="button" className="btn btn-small btn-outline" onClick={clearPicks}>
            Clear
          </button>
        </div>
        <div className="grid picks-grid">
          {picks.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </div>
    </section>
  )
}
