import { NextRequest, NextResponse } from 'next/server'

const SESSION_COOKIE = 'sedadmin_session'
const PUBLIC_PATHS = ['/login', '/api/auth']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const isPublic = PUBLIC_PATHS.some(p => pathname.startsWith(p))
  if (isPublic) return NextResponse.next()

  const session = request.cookies.get(SESSION_COOKIE)
  const adminSecret = process.env.ADMIN_SECRET ?? ''

  if (!session || session.value !== adminSecret) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|logo-sala-ai\\.png|logo-sedapps\\.png|.*\\.(?:png|jpg|jpeg|svg|webp|ico|css|js)).*)'],
}
