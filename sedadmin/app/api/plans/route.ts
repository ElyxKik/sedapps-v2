import { NextRequest, NextResponse } from 'next/server'
import { backendRequest } from '@/lib/sedapps-backend'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    return NextResponse.json(await backendRequest('/v1/admin/plans'))
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, id, payload } = body

    if (action === 'create') {
      return NextResponse.json(
        await backendRequest('/v1/admin/plans', {
          method: 'POST',
          body: JSON.stringify(payload),
        }),
      )
    }

    if (action === 'update' && id) {
      return NextResponse.json(
        await backendRequest(`/v1/admin/plans/${id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        }),
      )
    }

    if (action === 'delete' && id) {
      return NextResponse.json(
        await backendRequest(`/v1/admin/plans/${id}`, { method: 'DELETE' }),
      )
    }

    return NextResponse.json({ error: 'Action invalide' }, { status: 400 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
