'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  CalendarDays,
  Check,
  CreditCard,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Sparkles,
  Trash2,
  X,
  Zap,
} from 'lucide-react'

interface BillingPlan {
  id: string
  slug: string
  name: string
  description?: string
  billingInterval: 'month' | 'year'
  priceCents: number
  currency: string
  monthlyCredits: number
  isActive: boolean
  stripePriceId?: string
  sortOrder: number
}

interface PlanForm {
  slug: string
  name: string
  description: string
  billingInterval: 'month' | 'year'
  price: string
  currency: string
  monthlyCredits: string
  stripePriceId: string
  sortOrder: string
  isActive: boolean
}

const EMPTY_FORM: PlanForm = {
  slug: '',
  name: '',
  description: '',
  billingInterval: 'month',
  price: '',
  currency: 'EUR',
  monthlyCredits: '50',
  stripePriceId: '',
  sortOrder: '10',
  isActive: true,
}

function money(cents: number, currency: string) {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
    minimumFractionDigits: cents % 100 === 0 ? 0 : 2,
  }).format(cents / 100)
}

function slugify(value: string) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

export default function SubscriptionsPage() {
  const [plans, setPlans] = useState<BillingPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<BillingPlan | null>(null)
  const [form, setForm] = useState<PlanForm>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<BillingPlan | null>(null)
  const [deleting, setDeleting] = useState(false)

  const loadPlans = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/plans', { cache: 'no-store' })
      const data = await response.json()
      if (!response.ok || data.error) throw new Error(data.error || 'Chargement impossible')
      setPlans(data.plans ?? [])
    } catch (reason: any) {
      setError(reason.message || 'Chargement impossible')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadPlans() }, [])

  const stats = useMemo(() => ({
    active: plans.filter(plan => plan.isActive).length,
    monthly: plans.filter(plan => plan.billingInterval === 'month').length,
    yearly: plans.filter(plan => plan.billingInterval === 'year').length,
    maxCredits: Math.max(0, ...plans.map(plan => plan.monthlyCredits)),
  }), [plans])

  const openCreate = () => {
    setEditing(null)
    setForm(EMPTY_FORM)
    setError('')
    setModalOpen(true)
  }

  const openEdit = (plan: BillingPlan) => {
    setEditing(plan)
    setForm({
      slug: plan.slug,
      name: plan.name,
      description: plan.description ?? '',
      billingInterval: plan.billingInterval,
      price: (plan.priceCents / 100).toString(),
      currency: plan.currency,
      monthlyCredits: plan.monthlyCredits.toString(),
      stripePriceId: plan.stripePriceId ?? '',
      sortOrder: plan.sortOrder.toString(),
      isActive: plan.isActive,
    })
    setError('')
    setModalOpen(true)
  }

  const savePlan = async (event: FormEvent) => {
    event.preventDefault()
    const price = Number(form.price || 0)
    const credits = Number(form.monthlyCredits)
    if (!form.name.trim() || !form.slug.trim()) {
      setError('Le nom et le slug sont obligatoires.')
      return
    }
    if (!Number.isFinite(price) || price < 0 || !Number.isInteger(credits) || credits < 0) {
      setError('Le prix et les crédits doivent être des valeurs positives.')
      return
    }

    setSaving(true)
    setError('')
    try {
      const payload = {
        slug: slugify(form.slug),
        name: form.name.trim(),
        description: form.description.trim() || null,
        billingInterval: form.billingInterval,
        priceCents: Math.round(price * 100),
        currency: form.currency.toUpperCase(),
        monthlyCredits: credits,
        isActive: form.isActive,
        stripePriceId: form.stripePriceId.trim() || null,
        sortOrder: Number(form.sortOrder || 0),
      }
      const response = await fetch('/api/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: editing ? 'update' : 'create',
          id: editing?.id,
          payload,
        }),
      })
      const data = await response.json()
      if (!response.ok || data.error) throw new Error(data.error || 'Enregistrement impossible')
      setModalOpen(false)
      await loadPlans()
    } catch (reason: any) {
      setError(reason.message || 'Enregistrement impossible')
    } finally {
      setSaving(false)
    }
  }

  const deletePlan = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    setError('')
    try {
      const response = await fetch('/api/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'delete', id: deleteTarget.id }),
      })
      const data = await response.json()
      if (!response.ok || data.error) throw new Error(data.error || 'Suppression impossible')
      setDeleteTarget(null)
      await loadPlans()
    } catch (reason: any) {
      setError(reason.message || 'Suppression impossible')
      setDeleteTarget(null)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="p-5 md:p-8">
      <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-blue-300">
            <Sparkles className="h-4 w-4" /> Catalogue commercial
          </div>
          <h1 className="text-2xl font-bold text-white">Plans &amp; abonnements</h1>
          <p className="mt-1 max-w-2xl text-sm text-white/40">
            Créez vos offres mensuelles ou annuelles. Les crédits indiqués sont renouvelés chaque mois, même pour une facturation annuelle.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadPlans} className="rounded-xl border border-white/10 bg-white/5 p-2.5 text-white/50 transition hover:bg-white/10 hover:text-white" title="Actualiser">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button onClick={openCreate} className="flex items-center gap-2 rounded-xl bg-sala-primary px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500">
            <Plus className="h-4 w-4" /> Nouveau plan
          </button>
        </div>
      </div>

      {error && !modalOpen && (
        <div className="mb-5 flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <AlertCircle className="h-4 w-4" /> {error}
        </div>
      )}

      <div className="mb-7 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          { label: 'Plans actifs', value: stats.active, icon: Check, color: 'text-emerald-300 bg-emerald-500/10' },
          { label: 'Mensuels', value: stats.monthly, icon: CalendarDays, color: 'text-blue-300 bg-blue-500/10' },
          { label: 'Annuels', value: stats.yearly, icon: CreditCard, color: 'text-violet-300 bg-violet-500/10' },
          { label: 'Crédits max./mois', value: stats.maxCredits.toLocaleString('fr-FR'), icon: Zap, color: 'text-amber-300 bg-amber-500/10' },
        ].map(item => (
          <div key={item.label} className="glass rounded-2xl border border-white/5 p-4">
            <div className={`mb-3 flex h-9 w-9 items-center justify-center rounded-xl ${item.color}`}><item.icon className="h-4 w-4" /></div>
            <p className="text-xl font-bold text-white">{item.value}</p>
            <p className="mt-1 text-xs text-white/35">{item.label}</p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="glass flex min-h-64 items-center justify-center rounded-2xl text-white/35"><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Chargement des plans…</div>
      ) : plans.length === 0 ? (
        <div className="glass flex min-h-64 flex-col items-center justify-center rounded-2xl px-6 text-center">
          <CreditCard className="mb-3 h-10 w-10 text-white/15" />
          <p className="font-semibold text-white">Aucun plan configuré</p>
          <p className="mt-1 text-sm text-white/35">Créez votre première offre pour commencer.</p>
        </div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {plans.map(plan => (
            <article key={plan.id} className={`glass relative overflow-hidden rounded-2xl border p-5 ${plan.isActive ? 'border-white/8' : 'border-white/5 opacity-65'}`}>
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-bold text-white">{plan.name}</h2>
                    <span className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase ${plan.billingInterval === 'year' ? 'bg-violet-500/15 text-violet-300' : 'bg-blue-500/15 text-blue-300'}`}>
                      {plan.billingInterval === 'year' ? 'Annuel' : 'Mensuel'}
                    </span>
                    <span className={`rounded-full px-2 py-1 text-[10px] ${plan.isActive ? 'bg-emerald-500/10 text-emerald-300' : 'bg-white/5 text-white/35'}`}>
                      {plan.isActive ? 'Actif' : 'Masqué'}
                    </span>
                  </div>
                  <p className="mt-1 font-mono text-xs text-white/25">{plan.slug}</p>
                </div>
                <div className="flex shrink-0 gap-1">
                  <button onClick={() => openEdit(plan)} className="rounded-lg p-2 text-white/35 transition hover:bg-white/10 hover:text-blue-300" title="Modifier"><Pencil className="h-4 w-4" /></button>
                  <button disabled={plan.slug === 'free'} onClick={() => setDeleteTarget(plan)} className="rounded-lg p-2 text-white/35 transition hover:bg-red-500/10 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-20" title={plan.slug === 'free' ? 'Le plan gratuit ne peut pas être supprimé' : 'Supprimer'}><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>

              <p className="mt-4 min-h-10 text-sm leading-relaxed text-white/40">{plan.description || 'Aucune description.'}</p>
              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-white/[0.035] p-3">
                  <p className="text-xs text-white/30">Tarif</p>
                  <p className="mt-1 text-xl font-bold text-white">{money(plan.priceCents, plan.currency)}<span className="ml-1 text-xs font-normal text-white/30">/{plan.billingInterval === 'year' ? 'an' : 'mois'}</span></p>
                </div>
                <div className="rounded-xl bg-amber-500/[0.06] p-3">
                  <p className="text-xs text-white/30">Crédits inclus</p>
                  <p className="mt-1 text-xl font-bold text-amber-300">{plan.monthlyCredits.toLocaleString('fr-FR')}<span className="ml-1 text-xs font-normal text-white/30">/mois</span></p>
                </div>
              </div>
              {plan.stripePriceId && <p className="mt-3 truncate font-mono text-[11px] text-white/20">Stripe : {plan.stripePriceId}</p>}
            </article>
          ))}
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-950/80 p-4 backdrop-blur-sm">
          <form onSubmit={savePlan} className="glass my-8 w-full max-w-2xl rounded-3xl border border-white/10 p-6 shadow-2xl md:p-7">
            <div className="mb-6 flex items-start justify-between">
              <div><p className="text-xs font-semibold uppercase tracking-widest text-blue-300">Configuration</p><h2 className="mt-1 text-xl font-bold text-white">{editing ? 'Modifier le plan' : 'Créer un plan'}</h2></div>
              <button type="button" onClick={() => setModalOpen(false)} className="rounded-lg p-2 text-white/30 hover:bg-white/10 hover:text-white"><X className="h-5 w-5" /></button>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="text-xs text-white/45">Nom du plan
                <input required value={form.name} onChange={event => setForm(current => ({ ...current, name: event.target.value, slug: editing ? current.slug : slugify(event.target.value) }))} placeholder="Ex. Pro" className="mt-1.5 w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-3 text-sm text-white outline-none focus:border-blue-500/60" />
              </label>
              <label className="text-xs text-white/45">Slug
                <input required pattern="[a-z0-9-]+" value={form.slug} onChange={event => setForm(current => ({ ...current, slug: slugify(event.target.value) }))} placeholder="pro" className="mt-1.5 w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-3 font-mono text-sm text-white outline-none focus:border-blue-500/60" />
              </label>
            </div>

            <label className="mt-4 block text-xs text-white/45">Description
              <textarea rows={3} maxLength={1000} value={form.description} onChange={event => setForm(current => ({ ...current, description: event.target.value }))} placeholder="Pour qui est ce plan et que contient-il ?" className="mt-1.5 w-full resize-none rounded-xl border border-white/10 bg-white/5 px-3.5 py-3 text-sm text-white outline-none focus:border-blue-500/60" />
            </label>

            <div className="mt-4">
              <p className="mb-2 text-xs text-white/45">Période de facturation</p>
              <div className="grid grid-cols-2 gap-2 rounded-xl bg-white/[0.035] p-1.5">
                {(['month', 'year'] as const).map(interval => (
                  <button type="button" key={interval} onClick={() => setForm(current => ({ ...current, billingInterval: interval }))} className={`rounded-lg px-3 py-2.5 text-sm font-semibold transition ${form.billingInterval === interval ? 'bg-blue-600 text-white shadow-lg' : 'text-white/40 hover:text-white'}`}>
                    {interval === 'month' ? 'Mensuel' : 'Annuel'}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <label className="text-xs text-white/45">Prix ({form.currency})
                <input required type="number" min="0" step="0.01" value={form.price} onChange={event => setForm(current => ({ ...current, price: event.target.value }))} placeholder="29.00" className="mt-1.5 w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-3 text-sm text-white outline-none focus:border-blue-500/60" />
              </label>
              <label className="text-xs text-white/45">Devise
                <select value={form.currency} onChange={event => setForm(current => ({ ...current, currency: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-white/10 bg-slate-900 px-3.5 py-3 text-sm text-white outline-none focus:border-blue-500/60">
                  <option value="EUR">EUR</option><option value="USD">USD</option><option value="CDF">CDF</option>
                </select>
              </label>
              <label className="text-xs text-white/45">Crédits par mois
                <input required type="number" min="0" step="1" value={form.monthlyCredits} onChange={event => setForm(current => ({ ...current, monthlyCredits: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-3 text-sm text-white outline-none focus:border-blue-500/60" />
              </label>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="text-xs text-white/45">Stripe Price ID <span className="text-white/20">(facultatif)</span>
                <input value={form.stripePriceId} onChange={event => setForm(current => ({ ...current, stripePriceId: event.target.value }))} placeholder="price_…" className="mt-1.5 w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-3 font-mono text-sm text-white outline-none focus:border-blue-500/60" />
              </label>
              <label className="text-xs text-white/45">Ordre d’affichage
                <input type="number" min="0" step="1" value={form.sortOrder} onChange={event => setForm(current => ({ ...current, sortOrder: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-3 text-sm text-white outline-none focus:border-blue-500/60" />
              </label>
            </div>

            <button type="button" onClick={() => setForm(current => ({ ...current, isActive: !current.isActive }))} className="mt-5 flex w-full items-center justify-between rounded-xl border border-white/8 bg-white/[0.025] px-4 py-3 text-left">
              <span><span className="block text-sm font-medium text-white">Plan actif</span><span className="text-xs text-white/30">Visible et disponible pour les nouveaux abonnements.</span></span>
              <span className={`flex h-6 w-11 items-center rounded-full p-1 transition ${form.isActive ? 'bg-emerald-500' : 'bg-white/10'}`}><span className={`h-4 w-4 rounded-full bg-white transition ${form.isActive ? 'translate-x-5' : ''}`} /></span>
            </button>

            {error && <div className="mt-4 flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2.5 text-xs text-red-300"><AlertCircle className="h-4 w-4" />{error}</div>}

            <div className="mt-6 flex gap-3">
              <button type="button" onClick={() => setModalOpen(false)} className="flex-1 rounded-xl bg-white/5 px-4 py-3 text-sm text-white/55 transition hover:bg-white/10">Annuler</button>
              <button disabled={saving} className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-sala-primary px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:opacity-50">{saving && <Loader2 className="h-4 w-4 animate-spin" />}{editing ? 'Enregistrer' : 'Créer le plan'}</button>
            </div>
          </form>
        </div>
      )}

      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="glass w-full max-w-sm rounded-2xl border border-white/10 p-6">
            <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-red-500/10 text-red-300"><Trash2 className="h-5 w-5" /></div>
            <h2 className="text-lg font-bold text-white">Supprimer {deleteTarget.name} ?</h2>
            <p className="mt-2 text-sm text-white/40">Cette offre disparaîtra du catalogue. Vous pouvez aussi la modifier et la masquer.</p>
            <div className="mt-6 flex gap-3">
              <button onClick={() => setDeleteTarget(null)} className="flex-1 rounded-xl bg-white/5 px-4 py-3 text-sm text-white/55">Annuler</button>
              <button disabled={deleting} onClick={deletePlan} className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-red-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50">{deleting && <Loader2 className="h-4 w-4 animate-spin" />}Supprimer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
