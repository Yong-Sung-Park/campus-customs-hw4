import { Link } from 'react-router-dom'
import { formatPrice, shortDescription } from '../api.ts'

/** Works for both catalogue products and chat cards (which carry short_description). */
export interface CardProduct {
  product_id: string
  name: string
  price: number
  image_url: string
  category?: string
  description?: string
  short_description?: string
}

const CATEGORY_LABELS: Record<string, string> = {
  hoodie: 'Hoodie',
  crewneck: 'Crewneck',
  'quarter-zip': 'Quarter-zip',
  jacket: 'Jacket',
  't-shirt': 'Tee',
  'long-sleeve': 'Long-sleeve',
}

export default function ProductCard({ product }: { product: CardProduct }) {
  const blurb = product.short_description ?? shortDescription(product.description ?? '')
  const tag = product.category ? CATEGORY_LABELS[product.category] : undefined
  return (
    <Link to={`/products/${product.product_id}`} className="card">
      <div className="card-img">
        {tag && <span className="card-tag">{tag}</span>}
        <img src={product.image_url} alt={product.name} loading="lazy" />
        <span className="card-cta">View details →</span>
      </div>
      <div className="card-body">
        <h3>{product.name}</h3>
        <p className="card-desc">{blurb}</p>
        <p className="price">{formatPrice(product.price)}</p>
      </div>
    </Link>
  )
}
