import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { useChat } from '../chat.tsx'

const PRODUCT_PAGE_STARTERS = ['Is this in stock in M?', 'What colors does it come in?', 'Show me similar items']
const GENERAL_STARTERS = ['What hoodies do you have?', 'Gift ideas under $40', 'What’s good for winter?']

export default function ChatWidget() {
  const { open, setOpen, messages, sending, send } = useChat()
  const [input, setInput] = useState('')
  const listRef = useRef<HTMLDivElement>(null)
  const { pathname } = useLocation()
  const starters = /^\/products\/[^/]+$/.test(pathname) ? PRODUCT_PAGE_STARTERS : GENERAL_STARTERS

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, open, sending])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!input.trim() || sending) return
    void send(input)
    setInput('')
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Campus Customs chat">
          <header className="chat-header">
            <span className="chat-id">
              <span className="chat-avatar">CC</span>
              <span>
                Campus Customs Helper
                <small>
                  <i className="dot" /> Online · checks live stock
                </small>
              </span>
            </span>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>
          <div className="chat-messages" ref={listRef}>
            {messages.map((m, i) => (
              <div key={i} className={`msg msg-${m.role}${m.error ? ' msg-error' : ''}`}>
                {m.content}
                {m.products && m.products.length > 0 && (
                  <span className="msg-note">↑ {m.products.length} item{m.products.length > 1 ? 's' : ''} shown on the page</span>
                )}
              </div>
            ))}
            {sending && (
              <div className="msg msg-assistant msg-typing" aria-label="Assistant is typing">
                <span />
                <span />
                <span />
              </div>
            )}
          </div>
          <div className="chat-starters" aria-label="Suggested questions">
            {starters.map((q) => (
              <button key={q} type="button" className="starter" disabled={sending} onClick={() => void send(q)}>
                {q}
              </button>
            ))}
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about hoodies, sizes, prices…"
              aria-label="Chat message"
            />
            <button type="submit" className="btn" disabled={sending || !input.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className={`chat-bubble${open ? '' : ' chat-bubble-idle'}`}
        onClick={() => setOpen(!open)}
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? '×' : '💬'}
      </button>
    </div>
  )
}
