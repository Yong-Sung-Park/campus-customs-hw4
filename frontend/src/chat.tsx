import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { fetchChatHistory, sendChat, type ChatTurn, type PageInfo, type ProductCardData } from './api.ts'
import { useAuth } from './auth.tsx'

export interface ChatMessage extends ChatTurn {
  error?: boolean
  products?: ProductCardData[]
}

interface ChatState {
  open: boolean
  setOpen: (open: boolean) => void
  messages: ChatMessage[]
  sending: boolean
  send: (text: string) => Promise<void>
  /** Product cards from the latest chat answer, shown on the page. */
  picks: ProductCardData[]
  picksFor: string
  clearPicks: () => void
}

export const GREETING: ChatMessage = {
  role: 'assistant',
  content: 'Hi! I’m the Campus Customs helper. Ask me about our Yale gear, prices, or sizes.',
}

// How many earlier turns to send with each message (the server also caps this).
const HISTORY_TURNS = 12

const ChatContext = createContext<ChatState | null>(null)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING])
  const [sending, setSending] = useState(false)
  const [picks, setPicks] = useState<ProductCardData[]>([])
  const [picksFor, setPicksFor] = useState('')
  const messagesRef = useRef(messages)
  messagesRef.current = messages
  const { user } = useAuth()
  const location = useLocation()

  // Page context: tells the agent which product "this" means on a product page.
  const pageRef = useRef<PageInfo>({ path: '/', product_id: null })
  const productMatch = location.pathname.match(/^\/products\/([^/]+)$/)
  pageRef.current = { path: location.pathname, product_id: productMatch ? decodeURIComponent(productMatch[1]) : null }

  // Logged in: reload the saved conversation. Logged out: start fresh.
  const userId = user?.id ?? null
  useEffect(() => {
    setPicks([])
    if (userId === null) {
      setMessages([GREETING])
      return
    }
    let cancelled = false
    fetchChatHistory()
      .then(({ messages: saved }) => {
        if (cancelled) return
        const restored: ChatMessage[] = saved.map((m) => ({ role: m.role, content: m.content, products: m.products }))
        setMessages([GREETING, ...restored])
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [userId])

  const send = useCallback(async (raw: string) => {
    const text = raw.trim()
    if (!text) return
    // Earlier turns for context: skip the canned greeting and any error bubbles.
    const history: ChatTurn[] = messagesRef.current
      .filter((m) => m !== GREETING && !m.error)
      .slice(-HISTORY_TURNS)
      .map(({ role, content }) => ({ role, content }))
    setMessages((m) => [...m, { role: 'user', content: text }])
    setSending(true)
    try {
      const res = await sendChat(text, history, pageRef.current)
      // Don't replace the picks with a lone card for the product already on screen.
      const onlyCurrentItem = res.products.length === 1 && res.products[0].product_id === pageRef.current.product_id
      const shown = onlyCurrentItem ? [] : res.products
      setMessages((m) => [...m, { role: 'assistant', content: res.reply, products: shown }])
      if (shown.length > 0) {
        setPicks(res.products)
        setPicksFor(text)
      }
    } catch (err) {
      const message = (err as Error).message
      // Server errors carry a friendly `detail`; a network failure means the backend is down.
      const friendly = /^\d{3} |Failed to fetch|NetworkError/.test(message)
        ? 'Sorry, I couldn’t reach the shop server. Please try again in a moment.'
        : message
      setMessages((m) => [...m, { role: 'assistant', content: friendly, error: true }])
    } finally {
      setSending(false)
    }
  }, [])

  const clearPicks = useCallback(() => setPicks([]), [])

  return (
    <ChatContext.Provider value={{ open, setOpen, messages, sending, send, picks, picksFor, clearPicks }}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChat(): ChatState {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used inside <ChatProvider>')
  return ctx
}
