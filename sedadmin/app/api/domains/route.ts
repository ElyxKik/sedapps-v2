import { NextResponse } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'

export const dynamic = 'force-dynamic'

export async function GET() {
  const { data, error } = await supabaseAdmin
    .from('domains')
    .select('*')
    .order('created_at', { ascending: false })

  if (error) return NextResponse.json({ domains: [] })
  return NextResponse.json({ domains: data ?? [] })
}
