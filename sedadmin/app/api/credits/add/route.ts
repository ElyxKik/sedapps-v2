import { NextRequest, NextResponse } from 'next/server'
import { backendRequest } from '@/lib/sedapps-backend'

export async function POST(request: NextRequest) {
  try {
    const { userId, credits, description } = await request.json()

    if (!userId || !credits || credits <= 0) {
      return NextResponse.json(
        { error: 'userId et credits (> 0) sont requis' },
        { status: 400 }
      )
    }

    const data = await backendRequest('/v1/admin/credits/add', {
      method: 'POST',
      body: JSON.stringify({
        userId,
        credits,
        description: description || `Ajout manuel par admin`,
      }),
    })

    return NextResponse.json(data)
  } catch (err: any) {
    console.error('[Credits Admin API] Error:', err.message)
    return NextResponse.json(
      { error: err.message },
      { status: 500 }
    )
  }
}
