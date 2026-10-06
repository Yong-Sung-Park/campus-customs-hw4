import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type Product } from '../api.ts'
import ProductCard from '../components/ProductCard.tsx'

const FEATURED_IDS = [
  'basic-hoodie-big-yale',
  '2025-yale-vs-harvard-t-shirt',
  'champion-reverse-weave-crewneck',
  'benjamin-franklin-fleece-jacket',
]

const HERO_SHOTS = [
  { id: 'basic-hoodie-big-yale', caption: 'Library nights' },
  { id: '2025-yale-vs-harvard-t-shirt', caption: 'The Game' },
  { id: 'benjamin-franklin-fleece-jacket', caption: 'February walks' },
]

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts()
      .then((all) => setFeatured(FEATURED_IDS.map((id) => all.find((p) => p.product_id === id)).filter((p): p is Product => !!p)))
      .catch(() => setFeatured([]))
  }, [])

  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-copy">
          <p className="eyebrow">Yale gear from 57 Broadway</p>
          <h1>
            Wear your <em>Bulldog</em> pride.
          </h1>
          <p className="lead">
            Hoodies for late nights at the library, tees for game day, and fleece for the walk across Old Campus in
            February. Campus Customs has Yale apparel for students, alumni, and the families cheering them on.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-light">
              Shop the collection
            </Link>
            <Link to="/about" className="btn btn-ghost">
              Our story
            </Link>
          </div>
          </div>
          <div className="hero-collage" aria-hidden="true">
            {HERO_SHOTS.map((s, i) => (
              <figure key={s.id} className={`polaroid polaroid-${i + 1}`}>
                <img src={`/media/products/${s.id}.jpg`} alt="" />
                <figcaption>{s.caption}</figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="pillars">
          <div>
            <h3>For every college</h3>
            <p>Crewnecks and quarter-zips for each residential college, from Benjamin Franklin to Grace Hopper.</p>
          </div>
          <div>
            <h3>Game-day ready</h3>
            <p>Harvard–Yale tees, team left-chest hoodies, and classic Champion reverse weave for the stands.</p>
          </div>
          <div>
            <h3>Ask our helper</h3>
            <p>Not sure about a size or color? Tap the chat bubble in the corner and ask. Stock and prices come straight from our inventory.</p>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Bulldog favorites</h2>
          <Link to="/products">See all products →</Link>
        </div>
        <div className="grid">
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>
    </>
  )
}
