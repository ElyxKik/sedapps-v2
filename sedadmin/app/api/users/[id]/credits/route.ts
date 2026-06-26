import { NextRequest, NextResponse } from 'next/server'
import { backendRequest } from '@/lib/sedapps-backend'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: userId } = await params
    const data = await backendRequest(`/v1/admin/users/${encodeURIComponent(userId)}/credits`)
    return NextResponse.json(data)
  } catch (err: any) {
    console.error('[Credits API] Error:', err.message)
    return NextResponse.json(
      { error: err.message },
      { status: 500 }
    )
  }
}
