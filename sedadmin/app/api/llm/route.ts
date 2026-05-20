/**
 * Proxy to the main app's /api/admin/llm endpoint
 * using ADMIN_SECRET from env.
 */
import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

const MAIN_APP = (process.env.NEXT_PUBLIC_MAIN_APP_URL ?? 'http://localhost:3000').replace(/\/$/, '')
const ADMIN_SECRET = process.env.ADMIN_SECRET ?? ''

async function proxy(method: string, body?: unknown) {
  const res = await fetch(`${MAIN_APP}/api/admin/llm`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'x-admin-secret': ADMIN_SECRET,
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  })
  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}

export async function GET()                         { return proxy('GET') }
export async function POST(req: NextRequest)        { return proxy('POST', await req.json()) }
export async function DELETE()                      { return proxy('DELETE') }
