import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const search = searchParams.get('search') ?? ''
    const limit = Math.min(parseInt(searchParams.get('limit') ?? '50', 10), 100)

    // Get all users from auth.users
    let usersQuery = supabaseAdmin.auth.admin.listUsers()

    const { data: authUsers, error: authError } = await usersQuery

    if (authError) {
      console.error('[Credits Admin] Auth users error:', authError)
      return NextResponse.json(
        { error: `Erreur récupération utilisateurs: ${authError.message}` },
        { status: 500 }
      )
    }

    // Filter by search term
    let filtered = (authUsers?.users ?? [])
    if (search) {
      const searchLower = search.toLowerCase()
      filtered = filtered.filter(
        u =>
          u.email?.toLowerCase().includes(searchLower) ||
          u.user_metadata?.name?.toLowerCase().includes(searchLower)
      )
    }

    // Get credit balances for all users
    const { data: credits, error: creditsError } = await supabaseAdmin
      .from('user_credits')
      .select('user_id, balance, total_purchased, total_consumed')

    if (creditsError) {
      console.warn('[Credits Admin] Credits table error:', creditsError.message)
      // Continue without credits if table doesn't exist
    }

    const creditMap = new Map(
      (credits ?? []).map((c: any) => [c.user_id, c])
    )

    // Combine data
    const users = filtered.slice(0, limit).map((u: any) => {
      const creditData = creditMap.get(u.id)
      return {
        id: u.id,
        email: u.email,
        name: u.user_metadata?.name ?? 'N/A',
        createdAt: u.created_at,
        balance: creditData?.balance ?? 0,
        totalPurchased: creditData?.total_purchased ?? 0,
        totalConsumed: creditData?.total_consumed ?? 0,
      }
    })

    return NextResponse.json({ users, total: filtered.length })
  } catch (err: any) {
    console.error('[Credits Admin] Error:', err.message)
    return NextResponse.json(
      { error: err.message },
      { status: 500 }
    )
  }
}
