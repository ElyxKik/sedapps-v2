const BACKEND_URL = process.env.SEDAPPS_BACKEND_URL || process.env.NEXT_PUBLIC_CORE_API_BASE_URL || 'http://localhost:8000'
const ADMIN_SECRET = process.env.SEDAPPS_ADMIN_SECRET || process.env.ADMIN_SECRET || ''

export async function backendRequest(path: string, init: RequestInit = {}) {
  const url = `${BACKEND_URL.replace(/\/$/, '')}${path}`
  const headers = new Headers(init.headers)
  headers.set('X-Admin-Secret', ADMIN_SECRET)
  if (!headers.has('Content-Type') && init.body) headers.set('Content-Type', 'application/json')

  const response = await fetch(url, {
    ...init,
    headers,
    cache: 'no-store',
  })

  const text = await response.text()
  const data = text ? JSON.parse(text) : null
  if (!response.ok) {
    const message = data?.detail || data?.error || `Backend error ${response.status}`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return data
}
