import { NextRequest, NextResponse } from 'next/server'
import { backendRequest } from '@/lib/sedapps-backend'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const search = searchParams.get('search') ?? ''
    const limit = Math.min(parseInt(searchParams.get('limit') ?? '50', 10), 100)

    const data = await backendRequest(`/v1/admin/users?search=${encodeURIComponent(search)}&limit=${limit}`)
    return NextResponse.json(data)
  } catch (err: any) {
    console.error('[Credits Admin] Error:', err.message)
    return NextResponse.json(
      { error: err.message },
      { status: 500 }
    )
  }
}
