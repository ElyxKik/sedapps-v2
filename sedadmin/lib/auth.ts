import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

const ADMIN_SECRET = process.env.ADMIN_SECRET ?? ''
const SESSION_COOKIE = 'sedadmin_session'

export async function checkAdminSession(): Promise<boolean> {
  const cookieStore = await cookies()
  const session = cookieStore.get(SESSION_COOKIE)
  return session?.value === ADMIN_SECRET
}

export async function requireAdmin() {
  if (!(await checkAdminSession())) redirect('/login')
}

export function validateSecret(secret: string): boolean {
  return ADMIN_SECRET !== '' && secret === ADMIN_SECRET
}

export { SESSION_COOKIE }
