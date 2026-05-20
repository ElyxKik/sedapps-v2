import { NextRequest, NextResponse } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'

export const dynamic = 'force-dynamic'

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: userId } = await params

  const [userRes, projectsRes, subsRes, domainsRes] = await Promise.all([
    supabaseAdmin.auth.admin.getUserById(userId),
    supabaseAdmin
      .from('projects')
      .select('id, name, slug, domain, stack_type, status, visits, created_at')
      .eq('user_id', userId)
      .order('created_at', { ascending: false }),
    supabaseAdmin
      .from('subscriptions')
      .select('id, plan, status, current_period_end, cancel_at_period_end, stripe_subscription_id, stripe_customer_id, created_at')
      .eq('user_id', userId)
      .order('created_at', { ascending: false }),
    supabaseAdmin
      .from('domains')
      .select('id, domain, verified, created_at')
      .eq('user_id', userId)
      .order('created_at', { ascending: false }),
  ])

  if (userRes.error) {
    return NextResponse.json({ error: userRes.error.message }, { status: 404 })
  }

  return NextResponse.json({
    user: userRes.data.user,
    projects: projectsRes.data ?? [],
    subscriptions: subsRes.data ?? [],
    domains: domainsRes.data ?? [],
  })
}
