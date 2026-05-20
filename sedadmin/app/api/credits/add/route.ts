import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'

export async function POST(request: NextRequest) {
  try {
    const { userId, credits, description } = await request.json()

    if (!userId || !credits || credits <= 0) {
      return NextResponse.json(
        { error: 'userId et credits (> 0) sont requis' },
        { status: 400 }
      )
    }

    // Call the add_credits RPC function
    const { data, error } = await supabaseAdmin.rpc('add_credits', {
      p_user_id: userId,
      p_credits: credits,
      p_type: 'bonus',
      p_description: description || `Ajout manuel par admin`,
    })

    if (error) {
      console.error('[Credits Admin API] RPC error:', error)
      return NextResponse.json(
        { error: `Erreur RPC: ${error.message}` },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      newBalance: data,
      message: `${credits} crédits ajoutés à l'utilisateur`,
    })
  } catch (err: any) {
    console.error('[Credits Admin API] Error:', err.message)
    return NextResponse.json(
      { error: err.message },
      { status: 500 }
    )
  }
}
