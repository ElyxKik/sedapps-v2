import { NextResponse } from 'next/server'
import { supabaseAdmin } from '@/lib/supabase'

export const dynamic = 'force-dynamic'

const STRIPE_KEY = process.env.STRIPE_SECRET_KEY ?? ''

async function stripeGet(path: string) {
  if (!STRIPE_KEY || STRIPE_KEY.includes('REPLACE')) return null
  const res = await fetch(`https://api.stripe.com/v1${path}`, {
    headers: { Authorization: `Bearer ${STRIPE_KEY}` },
    cache: 'no-store',
  })
  if (!res.ok) return null
  return res.json()
}

export async function GET() {
  // Fetch subscriptions from Supabase
  const { data: subs } = await supabaseAdmin
    .from('subscriptions')
    .select('id, plan, status, stripe_subscription_id, stripe_customer_id, created_at, current_period_end, cancel_at_period_end, user_id')
    .order('created_at', { ascending: false })

  const rows = subs ?? []

  // Plan price map (euros) — used as fallback if Stripe not configured
  const PLAN_PRICES: Record<string, number> = {
    starter: 9,
    pro: 29,
    business: 79,
    enterprise: 199,
  }

  // Attempt to enrich with Stripe data
  let stripeCharges: { amount: number; currency: string; created: number }[] = []
  let stripeBalance: { available: { amount: number; currency: string }[] } | null = null

  const [chargesData, balanceData] = await Promise.all([
    stripeGet('/charges?limit=100'),
    stripeGet('/balance'),
  ])

  if (chargesData?.data) {
    stripeCharges = chargesData.data
      .filter((c: any) => c.paid && !c.refunded)
      .map((c: any) => ({ amount: c.amount, currency: c.currency, created: c.created }))
  }
  if (balanceData) stripeBalance = balanceData

  // Compute stats
  const activeSubs = rows.filter(s => s.status === 'active')
  const trialSubs  = rows.filter(s => s.status === 'trialing')
  const canceledSubs = rows.filter(s => s.status === 'canceled')

  // MRR from active subs using plan prices
  const mrr = activeSubs.reduce((sum, s) => sum + (PLAN_PRICES[s.plan] ?? 0), 0)
  const mrr_trial = trialSubs.reduce((sum, s) => sum + (PLAN_PRICES[s.plan] ?? 0), 0)

  // Revenue from Stripe charges
  const totalStripeRevenue = stripeCharges.reduce((sum, c) => sum + c.amount, 0) / 100

  // Revenue this month
  const startOfMonth = new Date()
  startOfMonth.setDate(1); startOfMonth.setHours(0, 0, 0, 0)
  const revenueThisMonth = stripeCharges
    .filter(c => new Date(c.created * 1000) >= startOfMonth)
    .reduce((sum, c) => sum + c.amount, 0) / 100

  // Revenue last month
  const startOfLastMonth = new Date(startOfMonth)
  startOfLastMonth.setMonth(startOfLastMonth.getMonth() - 1)
  const revenueLastMonth = stripeCharges
    .filter(c => {
      const d = new Date(c.created * 1000)
      return d >= startOfLastMonth && d < startOfMonth
    })
    .reduce((sum, c) => sum + c.amount, 0) / 100

  // ARR
  const arr = mrr * 12

  // Balance
  const balance = stripeBalance?.available?.[0]?.amount
    ? stripeBalance.available[0].amount / 100
    : null

  // Per-plan breakdown
  const planBreakdown: Record<string, { count: number; mrr: number }> = {}
  for (const s of activeSubs) {
    const p = s.plan ?? 'unknown'
    if (!planBreakdown[p]) planBreakdown[p] = { count: 0, mrr: 0 }
    planBreakdown[p].count++
    planBreakdown[p].mrr += PLAN_PRICES[p] ?? 0
  }

  return NextResponse.json({
    mrr,
    arr,
    mrr_trial,
    totalStripeRevenue,
    revenueThisMonth,
    revenueLastMonth,
    balance,
    stripeConfigured: !!(STRIPE_KEY && !STRIPE_KEY.includes('REPLACE')),
    counts: {
      active: activeSubs.length,
      trialing: trialSubs.length,
      canceled: canceledSubs.length,
      total: rows.length,
    },
    planBreakdown,
    subscriptions: rows,
  })
}
