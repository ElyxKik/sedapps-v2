import { NextRequest, NextResponse } from 'next/server'
import { validateSecret, SESSION_COOKIE } from '@/lib/auth'

export async function POST(request: NextRequest) {
  const { secret } = await request.json()
  if (!validateSecret(secret)) {
    return NextResponse.json({ error: 'Invalid secret' }, { status: 401 })
  }
  const res = NextResponse.json({ success: true })
  res.cookies.set(SESSION_COOKIE, secret, {
    httpOnly: true,
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 7, // 7 days
  })
  return res
}
