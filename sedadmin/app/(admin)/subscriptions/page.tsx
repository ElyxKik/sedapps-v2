'use client'

import { useEffect, useState } from 'react'
import { CreditCard, RefreshCw, ExternalLink, Search, TrendingUp, DollarSign, BarChart2, Loader2, AlertCircle, Plus, Pencil, Trash2, X } from 'lucide-react'

interface Sub {
  id: string
  user_id: string
  status: string
  plan: string
  current_period_end?: string
  cancel_at_period_end?: boolean
  stripe_customer_id?: string
  stripe_subscription_id?: string
  created_at: string
}

interface RevenueData {
  mrr: number
  arr: number
  mrr_trial: number
  totalStripeRevenue: number
  revenueThisMonth: number
  revenueLastMonth: number
  balance: number | null
  stripeConfigured: boolean
  counts: { active: number; trialing: number; canceled: number; total: number }
  planBreakdown: Record<string, { count: number; mrr: number }>
  subscriptions: Sub[]
}

const STATUS_COLORS: Record<string, string> = {
  active:     'bg-emerald-500/15 text-emerald-400',
  trialing:   'bg-blue-500/15 text-blue-400',
  past_due:   'bg-yellow-500/15 text-yellow-400',
  canceled:   'bg-red-500/15 text-red-400',
  incomplete: 'bg-white/10 text-white/40',
}

const PLAN_COLORS: Record<string, string> = {
  starter:    'bg-blue-500/15 text-blue-300',
  pro:        'bg-violet-500/15 text-violet-300',
  business:   'bg-orange-500/15 text-orange-300',
  enterprise: 'bg-emerald-500/15 text-emerald-300',
}

function fmt(n: number) {
  return n.toLocaleString('fr', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })
}

function StatCard({ label, value, sub, icon: Icon, color, loading }: {
  label: string; value: string; sub?: string; icon: any; color: string; loading?: boolean
}) {
  return (
    <div className="glass rounded-2xl p-5">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      {loading
        ? <div className="h-8 w-20 bg-white/5 rounded-lg animate-pulse mb-1" />
        : <p className="text-2xl font-bold text-white">{value}</p>}
      <p className="text-white/40 text-xs mt-1">{label}</p>
      {sub && <p className="text-xs text-emerald-400 mt-1">{sub}</p>}
    </div>
  )
}

const PLANS = ['starter', 'pro', 'business', 'enterprise']
const STATUSES = ['active', 'trialing', 'past_due', 'canceled', 'incomplete']
const PLAN_PRICES: Record<string, number> = { starter: 9, pro: 29, business: 79, enterprise: 199 }

type ModalMode = 'create' | 'edit' | null

interface FormState {
  user_id: string
  plan: string
  status: string
  current_period_end: string
  cancel_at_period_end: boolean
  stripe_subscription_id: string
  stripe_customer_id: string
}

const EMPTY_FORM: FormState = {
  user_id: '', plan: 'pro', status: 'active',
  current_period_end: '', cancel_at_period_end: false,
  stripe_subscription_id: '', stripe_customer_id: '',
}

export default function SubscriptionsPage() {
  const [data, setData] = useState<RevenueData | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [modal, setModal] = useState<ModalMode>(null)
  const [editSub, setEditSub] = useState<Sub | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<Sub | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    const res = await fetch('/api/revenue')
    const json = await res.json()
    setData(json)
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const openCreate = () => {
    setForm(EMPTY_FORM)
    setFormError('')
    setEditSub(null)
    setModal('create')
  }

  const openEdit = (s: Sub) => {
    setForm({
      user_id: s.user_id ?? '',
      plan: s.plan ?? 'pro',
      status: s.status ?? 'active',
      current_period_end: s.current_period_end ? s.current_period_end.slice(0, 10) : '',
      cancel_at_period_end: s.cancel_at_period_end ?? false,
      stripe_subscription_id: s.stripe_subscription_id ?? '',
      stripe_customer_id: s.stripe_customer_id ?? '',
    })
    setFormError('')
    setEditSub(s)
    setModal('edit')
  }

  const closeModal = () => { setModal(null); setEditSub(null); setFormError('') }

  const handleSave = async () => {
    if (!form.user_id.trim()) { setFormError('User ID requis'); return }
    if (!form.plan) { setFormError('Plan requis'); return }
    setSaving(true)
    setFormError('')
    const payload: Record<string, unknown> = {
      user_id: form.user_id.trim(),
      plan: form.plan,
      status: form.status,
      cancel_at_period_end: form.cancel_at_period_end,
      ...(form.current_period_end ? { current_period_end: new Date(form.current_period_end).toISOString() } : {}),
      ...(form.stripe_subscription_id ? { stripe_subscription_id: form.stripe_subscription_id.trim() } : {}),
      ...(form.stripe_customer_id ? { stripe_customer_id: form.stripe_customer_id.trim() } : {}),
    }
    const res = await fetch('/api/subscriptions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(modal === 'edit' ? { action: 'update', id: editSub!.id, payload } : { action: 'create', payload }),
    })
    const json = await res.json()
    if (json.error) { setFormError(json.error); setSaving(false); return }
    await fetchData()
    setSaving(false)
    closeModal()
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleteLoading(true)
    await fetch('/api/subscriptions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'delete', id: deleteTarget.id }),
    })
    await fetchData()
    setDeleteLoading(false)
    setDeleteTarget(null)
  }

  const subs = data?.subscriptions ?? []
  const filtered = subs.filter(s =>
    s.user_id?.includes(search) ||
    s.plan?.toLowerCase().includes(search.toLowerCase()) ||
    s.status?.toLowerCase().includes(search.toLowerCase()) ||
    s.stripe_subscription_id?.includes(search)
  )

  const growthPct = data && data.revenueLastMonth > 0
    ? Math.round(((data.revenueThisMonth - data.revenueLastMonth) / data.revenueLastMonth) * 100)
    : null

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <CreditCard className="w-6 h-6 text-orange-400" />
            Abonnements &amp; Revenus
          </h1>
          <p className="text-white/40 text-sm mt-1">{data?.counts.total ?? '…'} abonnements au total</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white text-sm font-semibold transition-all">
            <Plus className="w-4 h-4" /> Nouvel abonnement
          </button>
          <button onClick={fetchData} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-sm transition-all">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Stripe not configured warning */}
      {data && !data.stripeConfigured && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-yellow-500/8 border border-yellow-500/20 text-yellow-300 text-xs mb-5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          Clé Stripe non configurée — les montants proviennent des prix de plan par défaut. Ajoutez <code className="font-mono bg-white/10 px-1 rounded">STRIPE_SECRET_KEY</code> dans <code className="font-mono bg-white/10 px-1 rounded">sedadmin/.env.local</code>.
        </div>
      )}

      {/* Revenue KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="MRR (actifs)" value={loading ? '…' : fmt(data?.mrr ?? 0)} icon={DollarSign} color="bg-emerald-600" loading={loading}
          sub={data?.mrr_trial ? `+ ${fmt(data.mrr_trial)} en essai` : undefined} />
        <StatCard label="ARR estimé" value={loading ? '…' : fmt(data?.arr ?? 0)} icon={TrendingUp} color="bg-violet-600" loading={loading} />
        <StatCard label="Ce mois (Stripe)" value={loading ? '…' : fmt(data?.revenueThisMonth ?? 0)} icon={BarChart2} color="bg-blue-600" loading={loading}
          sub={growthPct !== null ? `${growthPct >= 0 ? '+' : ''}${growthPct}% vs mois dernier` : undefined} />
        <StatCard label="Solde Stripe" value={loading ? '…' : data?.balance !== null && data?.balance !== undefined ? fmt(data.balance) : 'N/A'} icon={CreditCard} color="bg-orange-600" loading={loading} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-6">
        {/* Abonnements par statut */}
        <div className="glass rounded-2xl p-5">
          <h2 className="text-xs font-semibold text-white/50 mb-3">Par statut</h2>
          <div className="space-y-2">
            {[
              { label: 'Actifs', key: 'active', color: 'text-emerald-400', bar: 'bg-emerald-500' },
              { label: 'En essai', key: 'trialing', color: 'text-blue-400', bar: 'bg-blue-500' },
              { label: 'Annulés', key: 'canceled', color: 'text-red-400', bar: 'bg-red-500' },
            ].map(({ label, key, color, bar }) => {
              const val = data?.counts[key as keyof typeof data.counts] ?? 0
              const total = data?.counts.total || 1
              return (
                <div key={key}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-white/50">{label}</span>
                    <span className={`font-semibold ${color}`}>{val}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <div className={`h-full rounded-full ${bar}`} style={{ width: `${Math.round((val / total) * 100)}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Revenus par plan */}
        <div className="glass rounded-2xl p-5 lg:col-span-2">
          <h2 className="text-xs font-semibold text-white/50 mb-3">Revenus par plan</h2>
          {loading || !data ? (
            <div className="space-y-2">
              {[1,2,3].map(i => <div key={i} className="h-8 bg-white/5 rounded-lg animate-pulse" />)}
            </div>
          ) : Object.keys(data.planBreakdown).length === 0 ? (
            <p className="text-white/30 text-sm">Aucun abonnement actif</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(data.planBreakdown)
                .sort((a, b) => b[1].mrr - a[1].mrr)
                .map(([plan, info]) => (
                  <div key={plan} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                    <div className="flex items-center gap-2">
                      <span className={`badge capitalize ${PLAN_COLORS[plan] ?? 'bg-white/8 text-white/50'}`}>{plan}</span>
                      <span className="text-white/40 text-xs">{info.count} abonné{info.count > 1 ? 's' : ''}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-semibold text-sm">{fmt(info.mrr)}<span className="text-white/30 text-xs font-normal">/mois</span></p>
                      <p className="text-white/30 text-xs">{fmt(info.mrr * 12)}/an</p>
                    </div>
                  </div>
                ))}
              <div className="flex items-center justify-between pt-2 mt-1">
                <span className="text-white/40 text-xs font-semibold">Total MRR</span>
                <span className="text-white font-bold">{fmt(data.mrr)}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <input
          type="text"
          placeholder="Rechercher par user ID, plan, statut, Stripe ID..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-white text-sm placeholder-white/25 focus:outline-none focus:border-violet-500/50"
        />
      </div>

      {/* Table */}
      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/8">
              <th className="text-left px-4 py-3 text-white/40 font-medium">User ID</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium">Plan</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium">Statut</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium">Montant/mois</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium hidden lg:table-cell">Renouvellement</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium hidden lg:table-cell">Stripe</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={6} className="text-center py-8 text-white/30"><Loader2 className="w-4 h-4 animate-spin inline mr-2" />Chargement…</td></tr>}
            {!loading && filtered.length === 0 && <tr><td colSpan={6} className="text-center py-8 text-white/30">Aucun abonnement</td></tr>}
            {filtered.map(s => {
              const PLAN_PRICES: Record<string, number> = { starter: 9, pro: 29, business: 79, enterprise: 199 }
              const amount = PLAN_PRICES[s.plan]
              return (
                <tr key={s.id} className="border-b border-white/5 hover:bg-white/5 transition-colors group">
                  <td className="px-4 py-3 font-mono text-white/60 text-xs">{s.user_id?.slice(0, 14)}…</td>
                  <td className="px-4 py-3">
                    <span className={`badge capitalize ${PLAN_COLORS[s.plan] ?? 'bg-white/8 text-white/40'}`}>{s.plan ?? 'free'}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`badge ${STATUS_COLORS[s.status] ?? 'bg-white/5 text-white/40'}`}>
                      {s.status}{s.cancel_at_period_end && ' ↓'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {amount !== undefined
                      ? <span className="text-white/80 font-semibold">{fmt(amount)}</span>
                      : <span className="text-white/25">—</span>}
                  </td>
                  <td className="px-4 py-3 text-white/40 text-xs hidden lg:table-cell">
                    {s.current_period_end ? new Date(s.current_period_end).toLocaleDateString('fr') : '—'}
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell">
                    <div className="flex gap-2">
                      {s.stripe_subscription_id && (
                        <a href={`https://dashboard.stripe.com/subscriptions/${s.stripe_subscription_id}`}
                          target="_blank" rel="noopener noreferrer"
                          className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1">
                          Sub <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                      {s.stripe_customer_id && (
                        <a href={`https://dashboard.stripe.com/customers/${s.stripe_customer_id}`}
                          target="_blank" rel="noopener noreferrer"
                          className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                          Client <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => openEdit(s)}
                        className="p-1.5 rounded-lg text-white/40 hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                        title="Modifier">
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => setDeleteTarget(s)}
                        className="p-1.5 rounded-lg text-white/40 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        title="Supprimer">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Create / Edit Modal */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass rounded-2xl p-6 w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-white">
                {modal === 'create' ? 'Nouvel abonnement' : "Modifier l'abonnement"}
              </h2>
              <button onClick={closeModal} className="text-white/30 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs text-white/50 mb-1.5">User ID <span className="text-red-400">*</span></label>
                <input
                  value={form.user_id}
                  onChange={e => setForm(f => ({ ...f, user_id: e.target.value }))}
                  placeholder="UUID de l'utilisateur"
                  disabled={modal === 'edit'}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm placeholder-white/20 focus:outline-none focus:border-violet-500/50 disabled:opacity-40 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-white/50 mb-1.5">Plan <span className="text-red-400">*</span></label>
                  <select
                    value={form.plan}
                    onChange={e => setForm(f => ({ ...f, plan: e.target.value }))}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-violet-500/50"
                  >
                    {PLANS.map(p => <option key={p} value={p} className="bg-zinc-900 capitalize">{p}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-white/50 mb-1.5">Statut</label>
                  <select
                    value={form.status}
                    onChange={e => setForm(f => ({ ...f, status: e.target.value }))}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-violet-500/50"
                  >
                    {STATUSES.map(s => <option key={s} value={s} className="bg-zinc-900">{s}</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs text-white/50 mb-1.5">Fin de période</label>
                <input
                  type="date"
                  value={form.current_period_end}
                  onChange={e => setForm(f => ({ ...f, current_period_end: e.target.value }))}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-violet-500/50"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-white/50 mb-1.5">Stripe Subscription ID</label>
                  <input
                    value={form.stripe_subscription_id}
                    onChange={e => setForm(f => ({ ...f, stripe_subscription_id: e.target.value }))}
                    placeholder="sub_…"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-xs placeholder-white/20 focus:outline-none focus:border-violet-500/50 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs text-white/50 mb-1.5">Stripe Customer ID</label>
                  <input
                    value={form.stripe_customer_id}
                    onChange={e => setForm(f => ({ ...f, stripe_customer_id: e.target.value }))}
                    placeholder="cus_…"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-xs placeholder-white/20 focus:outline-none focus:border-violet-500/50 font-mono"
                  />
                </div>
              </div>

              <label className="flex items-center gap-3 cursor-pointer select-none">
                <div
                  onClick={() => setForm(f => ({ ...f, cancel_at_period_end: !f.cancel_at_period_end }))}
                  className={`w-10 h-5 rounded-full transition-colors flex items-center px-0.5 ${form.cancel_at_period_end ? 'bg-orange-500' : 'bg-white/10'}`}
                >
                  <div className={`w-4 h-4 rounded-full bg-white transition-transform ${form.cancel_at_period_end ? 'translate-x-5' : 'translate-x-0'}`} />
                </div>
                <span className="text-sm text-white/60">Annulation prévue en fin de période</span>
              </label>

              {PLAN_PRICES[form.plan] && (
                <div className="flex items-center gap-2 text-xs text-white/40 bg-white/3 rounded-xl px-3 py-2">
                  <CreditCard className="w-3.5 h-3.5" />
                  Montant : <span className="text-white/70 font-semibold">{fmt(PLAN_PRICES[form.plan])}/mois</span>
                  <span className="text-white/25">·</span>
                  <span className="text-white/50">{fmt(PLAN_PRICES[form.plan] * 12)}/an</span>
                </div>
              )}

              {formError && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                  <AlertCircle className="w-3.5 h-3.5" /> {formError}
                </div>
              )}
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={closeModal} className="flex-1 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 text-sm transition-colors">
                Annuler
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white text-sm font-semibold transition-colors flex items-center justify-center gap-2"
              >
                {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                {modal === 'create' ? 'Créer' : 'Enregistrer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirm Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass rounded-2xl p-6 w-full max-w-sm shadow-2xl">
            <div className="w-12 h-12 rounded-2xl bg-red-500/15 flex items-center justify-center mb-4">
              <Trash2 className="w-6 h-6 text-red-400" />
            </div>
            <h2 className="text-lg font-bold text-white mb-2">Supprimer l&apos;abonnement ?</h2>
            <p className="text-white/40 text-sm mb-1">
              Plan <span className="text-white/70 capitalize font-semibold">{deleteTarget.plan}</span>
            </p>
            <p className="text-white/30 text-xs font-mono mb-2">{deleteTarget.user_id}</p>
            <p className="text-yellow-400/70 text-xs mb-5 flex items-start gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              Supprime uniquement l&apos;enregistrement en base. L&apos;abonnement Stripe reste actif.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setDeleteTarget(null)} className="flex-1 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 text-sm transition-colors">
                Annuler
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteLoading}
                className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-sm font-semibold transition-colors flex items-center justify-center gap-2"
              >
                {deleteLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                Supprimer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
