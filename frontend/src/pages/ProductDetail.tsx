import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type Product } from '../api.ts'
import { useChat } from '../chat.tsx'

export default function ProductDetail() {
  const { id = '' } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { setOpen, send, sending } = useChat()

  useEffect(() => {
    setProduct(null)
    setError(null)
    fetchProduct(id)
      .then(setProduct)
      .catch((e: Error) => setError(e.message))
  }, [id])

  if (error) {
    return (
      <section className="section">
        <p className="error">We couldn’t find that product ({error}).</p>
        <Link to="/products">← Back to all products</Link>
      </section>
    )
  }
  if (!product) {
    return (
      <section className="section">
        <p className="muted">Loading…</p>
      </section>
    )
  }

  return (
    <section className="section">
      <Link to="/products" className="back-link">
        ← All products
      </Link>
      <div className="detail">
        <div className="detail-img">
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price price-lg">{formatPrice(product.price)}</p>
          <button
            type="button"
            className="btn btn-ask"
            disabled={sending}
            onClick={() => {
              setOpen(true)
              void send('Which sizes of this are in stock right now?')
            }}
          >
            💬 Ask about this item
          </button>
          <p>{product.description}</p>

          <h3>Colors</h3>
          <div className="chips">
            {product.colors.map((c) => (
              <span key={c} className="chip">
                {c}
              </span>
            ))}
          </div>

          <h3>Sizes &amp; stock</h3>
          <ul className="sizes">
            {product.inventory?.map((s) => (
              <li key={s.size} className={s.quantity === 0 ? 'size sold-out' : 'size'}>
                <strong>{s.size}</strong>
                <span>{s.quantity === 0 ? 'Sold out' : `${s.quantity} in stock`}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
