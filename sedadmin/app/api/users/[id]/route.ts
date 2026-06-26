import { NextRequest, NextResponse } from 'next/server'
import { backendRequest } from '@/lib/sedapps-backend'

export const dynamic = 'force-dynamic'

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: userId } = await params
    const data = await backendRequest(`/v1/admin/users/${encodeURIComponent(userId)}`)
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
