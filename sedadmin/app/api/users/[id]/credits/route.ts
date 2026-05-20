import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const userId = params.id

    // Get credit balance
    const { data: creditBalance, error: balanceError } = await supabaseAdmin
      .from('user_credits')
      .select('balance, total_purchased, total_consumed')
      .eq('user_id', userId)
      .single()

    if (balanceError && balanceError.code !== 'PGRST116') {
      console.error('[Credits API] Balance error:', balanceError)
      return NextResponse.json(
        { error: balanceError.message },
        { status: 500 }
      )
    }

    // Get transaction history
    const { data: transactions, error: transError } = await supabaseAdmin
      .from('credit_transactions')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(20)

    if (transError && transError.code !== 'PGRST116') {
      console.error('[Credits API] Transactions error:', transError)
      return NextResponse.json(
        { error: transError.message },
        { status: 500 }
      )
    }

    return NextResponse.json({
      balance: creditBalance || { balance: 0, total_purchased: 0, total_consumed: 0 },
      transactions: transactions || [],
    })
  } catch (err: any) {
    console.error('[Credits API] Error:', err.message)
    return NextResponse.json(
      { error: err.message },
      { status: 500 }
    )
  }
}
