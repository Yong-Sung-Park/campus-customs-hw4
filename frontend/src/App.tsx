import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import NavBar from './components/NavBar.tsx'
import Ticker from './components/Ticker.tsx'
import Footer from './components/Footer.tsx'
import ChatWidget from './components/ChatWidget.tsx'
import ChatPicks from './components/ChatPicks.tsx'
import Home from './pages/Home.tsx'
import Products from './pages/Products.tsx'
import ProductDetail from './pages/ProductDetail.tsx'
import About from './pages/About.tsx'
import Login from './pages/Login.tsx'
import Signup from './pages/Signup.tsx'
import NotFound from './pages/NotFound.tsx'

export default function App() {
  const { pathname } = useLocation()

  // New page starts at the top (React Router keeps the old scroll position otherwise).
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return (
    <div className="app">
      <NavBar />
      <Ticker />
      <main className="main">
        <ChatPicks />
        {/* keyed by path so each page fades in on navigation */}
        <div className="page" key={pathname}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:id" element={<ProductDetail />} />
            <Route path="/about" element={<About />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </main>
      <Footer />
      <ChatWidget />
    </div>
  )
}
