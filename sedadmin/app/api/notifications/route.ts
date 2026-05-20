import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'

export const dynamic = 'force-dynamic'

export async function POST(request: NextRequest) {
  const { title, message, target } = await request.json()
  if (!title || !message) return NextResponse.json({ error: 'title and message required' }, { status: 400 })

  const { error } = await supabaseAdmin.from('notifications').insert({
    title,
    message,
    target,
    created_at: new Date().toISOString(),
  })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ success: true })
}
