import { useEffect, useMemo, useState } from 'react'
import { fetchProducts, type Product } from '../api.ts'
import ProductCard from '../components/ProductCard.tsx'

const CATEGORIES = [
  { key: 'all', label: 'All' },
  { key: 'hoodie', label: 'Hoodies' },
  { key: 'crewneck', label: 'Crewnecks' },
  { key: 'quarter-zip', label: 'Quarter-zips' },
  { key: 'jacket', label: 'Jackets' },
  { key: 't-shirt', label: 'Tees' },
  { key: 'long-sleeve', label: 'Long-sleeve' },
]
const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
type Sort = 'featured' | 'price-asc' | 'price-desc'

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('all')
  const [size, setSize] = useState('')
  const [sort, setSort] = useState<Sort>('featured')

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch((e: Error) => setError(e.message))
  }, [])

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: products?.length ?? 0 }
    products?.forEach((p) => (c[p.category] = (c[p.category] ?? 0) + 1))
    return c
  }, [products])

  const shown = useMemo(() => {
    if (!products) return []
    const words = query.toLowerCase().split(/\s+/).filter(Boolean)
    const list = products.filter((p) => {
      if (category !== 'all' && p.category !== category) return false
      if (size && !p.sizes_in_stock?.includes(size)) return false
      const haystack = `${p.name} ${p.description} ${p.colors.join(' ')} ${p.search_tags.join(' ')}`.toLowerCase()
      return words.every((w) => haystack.includes(w))
    })
    if (sort === 'price-asc') list.sort((a, b) => a.price - b.price)
    if (sort === 'price-desc') list.sort((a, b) => b.price - a.price)
    return list
  }, [products, query, category, size, sort])

  function reset() {
    setQuery('')
    setCategory('all')
    setSize('')
    setSort('featured')
  }

  return (
    <section className="section">
      <div className="section-head">
        <div>
          <h1>Shop all Yale gear</h1>
          {products && (
            <p className="muted">
              Showing {shown.length} of {products.length} items
            </p>
          )}
        </div>
      </div>

      <div className="finder">
        <input
          className="finder-search"
          type="search"
          placeholder="Search: bulldog, navy, hockey, Grace Hopper…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search products"
        />
        <select value={size} onChange={(e) => setSize(e.target.value)} aria-label="Only show items with my size in stock">
          <option value="">My size in stock: any</option>
          {SIZES.map((s) => (
            <option key={s} value={s}>
              {s} in stock
            </option>
          ))}
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value as Sort)} aria-label="Sort products">
          <option value="featured">Sort: Featured</option>
          <option value="price-asc">Price: low to high</option>
          <option value="price-desc">Price: high to low</option>
        </select>
      </div>
      <div className="chips finder-chips" role="group" aria-label="Filter by category">
        {CATEGORIES.map((c) => (
          <button
            key={c.key}
            type="button"
            className={`chip chip-btn${category === c.key ? ' active' : ''}`}
            onClick={() => setCategory(c.key)}
            aria-pressed={category === c.key}
          >
            {c.label} <span className="chip-count">{counts[c.key] ?? 0}</span>
          </button>
        ))}
      </div>

      {error && <p className="error">Couldn’t load products ({error}). Is the backend running on port 8000?</p>}
      {!products && !error && <p className="muted">Loading products…</p>}
      {products && shown.length === 0 && (
        <p className="muted">
          Nothing matches those filters.{' '}
          <button type="button" className="link-btn" onClick={reset}>
            Reset filters
          </button>
        </p>
      )}
      <div className="grid">
        {shown.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
    </section>
  )
}
