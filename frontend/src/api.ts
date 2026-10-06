export interface SizeStock {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  category: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  total_stock: number
  sizes_in_stock?: string[]
  inventory?: SizeStock[]
}

export interface ProductCardData {
  product_id: string
  name: string
  price: number
  image_url: string
  short_description: string
}

export interface ChatReply {
  reply: string
  products: ProductCardData[]
}

export interface User {
  id: number
  first_name: string
  last_name: string
  name: string
  email: string
}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    // FastAPI errors look like {"detail": "..."}; surface that message when present.
    let message = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') message = body.detail
    } catch {
      /* not JSON */
    }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

function postJson<T>(url: string, body: unknown): Promise<T> {
  return getJson<T>(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function fetchMe(): Promise<{ user: User | null }> {
  return getJson('/api/me')
}

export function login(email: string, password: string): Promise<{ user: User }> {
  return postJson('/api/auth/login', { email, password })
}

export interface SignupInput {
  first_name: string
  last_name: string
  email: string
  password: string
}

export function signup(input: SignupInput): Promise<{ user: User }> {
  return postJson('/api/auth/signup', input)
}

export function logout(): Promise<{ ok: boolean }> {
  return postJson('/api/auth/logout', {})
}

export function fetchProducts(): Promise<Product[]> {
  return getJson<Product[]>('/api/products')
}

export function fetchProduct(id: string): Promise<Product> {
  return getJson<Product>(`/api/products/${encodeURIComponent(id)}`)
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface PageInfo {
  path: string
  product_id: string | null
}

export function sendChat(message: string, history: ChatTurn[], page: PageInfo): Promise<ChatReply> {
  return postJson<ChatReply>('/api/chat', { message, history, page })
}

export interface SavedMessage extends ChatTurn {
  products: ProductCardData[]
  created_at: string
}

export function fetchChatHistory(): Promise<{ messages: SavedMessage[] }> {
  return getJson('/api/chat/history')
}

export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`
}

export function shortDescription(text: string, max = 90): string {
  if (text.length <= max) return text
  return text.slice(0, text.lastIndexOf(' ', max)) + '…'
}
