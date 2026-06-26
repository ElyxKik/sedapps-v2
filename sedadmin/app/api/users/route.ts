import { NextRequest, NextResponse } from 'next/server'
import { backendRequest } from '@/lib/sedapps-backend'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const search = searchParams.get('search') ?? ''
    const limit = searchParams.get('limit') ?? '100'
    const data = await backendRequest(`/v1/admin/users?search=${encodeURIComponent(search)}&limit=${encodeURIComponent(limit)}`)
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const data = await backendRequest('/v1/admin/users/actions', {
      method: 'POST',
      body: JSON.stringify(body),
    })
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
