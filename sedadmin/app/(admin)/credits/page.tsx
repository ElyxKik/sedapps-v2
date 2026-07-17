'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  AlertCircle,
  CheckCircle2,
  Coins,
  Eye,
  Gift,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  TrendingDown,
  WalletCards,
  X,
  Zap,
} from 'lucide-react'

interface CreditUser {
  id: string
  email: string
  name: string
  createdAt: string
  organization_id?: string
  organization_name?: string
  plan: string
  balance: number
  includedQuota: number
  includedRemaining: number
  bonusBalance: number
  reserved: number
  usedThisMonth: number
  totalPurchased: number
  totalConsumed: number
  totalTokens: number
}

const number = new Intl.NumberFormat('fr-FR')

export default function CreditsAdminPage() {
  const router = useRouter()
  const [users, setUsers] = useState<CreditUser[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selectedUser, setSelectedUser] = useState<CreditUser | null>(null)
  const [creditsToAdd, setCreditsToAdd] = useState('')
  const [description, setDescription] = useState('')
  const [grantType, setGrantType] = useState<'manual' | 'promotion'>('manual')
  const [submitting, setSubmitting] = useState(false)

  const fetchUsers = async (term = search) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(
        `/api/credits/users?search=${encodeURIComponent(term)}&limit=100`,
      )
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Impossible de charger les crédits.')
      setUsers(data.users ?? [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inattendue.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => fetchUsers(search), 300)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search])

  const totals = useMemo(
    () => {
      const organizations = new Map<string, CreditUser>()
      for (const user of users) {
        organizations.set(user.organization_id || user.id, user)
      }
      const wallets = [...organizations.values()]
      return {
        available: wallets.reduce((sum, user) => sum + user.balance, 0),
        bonus: wallets.reduce((sum, user) => sum + user.bonusBalance, 0),
        used: wallets.reduce((sum, user) => sum + user.usedThisMonth, 0),
      }
    },
    [users],
  )

  const closeModal = () => {
    setSelectedUser(null)
    setCreditsToAdd('')
    setDescription('')
    setGrantType('manual')
  }

  const openGrant = (user: CreditUser, type: 'manual' | 'promotion') => {
    setSelectedUser(user)
    setGrantType(type)
    setDescription(type === 'promotion' ? 'Bonus promotionnel de bienvenue' : '')
  }

  const handleAddCredits = async (event: FormEvent) => {
    event.preventDefault()
    const credits = Number.parseInt(creditsToAdd, 10)
    if (!selectedUser || !Number.isFinite(credits) || credits <= 0) return
    setSubmitting(true)
    setError(null)
    setSuccess(null)
    try {
      const response = await fetch('/api/credits/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: selectedUser.id,
          credits,
          type: grantType,
          description: description.trim() || undefined,
        }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Échec de l’ajout de crédits.')
      setSuccess(data.message)
      closeModal()
      await fetchUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inattendue.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-white">
            <Zap className="h-8 w-8 text-amber-400" />
            Crédits IA
          </h1>
          <p className="mt-2 text-sm text-white/50">
            1 crédit = 1 000 tokens · bonus, promotions et consommation réelle par utilisateur
          </p>
        </div>
        <button
          onClick={() => fetchUsers()}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white/70 transition hover:bg-white/10 hover:text-white"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Actualiser
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          { label: 'Total utilisable', value: totals.available, icon: WalletCards, color: 'text-amber-400' },
          { label: 'Crédits réellement ajoutés', value: totals.bonus, icon: Gift, color: 'text-violet-400' },
          { label: 'Consommés ce mois', value: totals.used, icon: TrendingDown, color: 'text-rose-400' },
        ].map(card => (
          <div key={card.label} className="glass rounded-2xl border border-white/5 p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm text-white/45">{card.label}</p>
              <card.icon className={`h-5 w-5 ${card.color}`} />
            </div>
            <p className={`mt-3 text-3xl font-bold ${card.color}`}>{number.format(card.value)}</p>
          </div>
        ))}
      </div>

      <div className="relative">
        <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-white/30" />
        <input
          value={search}
          onChange={event => setSearch(event.target.value)}
          placeholder="Rechercher par email ou nom…"
          className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-12 pr-4 text-sm text-white outline-none placeholder:text-white/25 focus:border-sala-primary/60"
        />
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
          <AlertCircle className="h-5 w-5 shrink-0" /> {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-300">
          <CheckCircle2 className="h-5 w-5 shrink-0" /> {success}
        </div>
      )}

      <div className="glass overflow-hidden rounded-2xl border border-white/5">
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-16 text-white/40">
            <Loader2 className="h-5 w-5 animate-spin" /> Chargement…
          </div>
        ) : users.length === 0 ? (
          <div className="py-16 text-center text-white/40">Aucun utilisateur trouvé.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1180px] text-sm">
              <thead className="border-b border-white/10 bg-white/[0.02] text-xs uppercase tracking-wide text-white/35">
                <tr>
                  <th className="px-5 py-4 text-left font-medium">Utilisateur</th>
                  <th className="px-4 py-4 text-left font-medium">Plan</th>
                  <th className="px-4 py-4 text-right font-medium">Total utilisable</th>
                  <th className="px-4 py-4 text-right font-medium">Quota plan restant</th>
                  <th className="px-4 py-4 text-right font-medium">Crédits ajoutés</th>
                  <th className="px-4 py-4 text-right font-medium">Utilisé ce mois</th>
                  <th className="px-4 py-4 text-right font-medium">Tokens suivis</th>
                  <th className="px-5 py-4 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr key={user.id} className="border-b border-white/5 transition hover:bg-white/[0.03]">
                    <td className="px-5 py-4">
                      <p className="font-medium text-white">{user.name}</p>
                      <p className="text-xs text-white/40">{user.email}</p>
                      <p className="mt-1 text-[11px] text-white/25">{user.organization_name}</p>
                    </td>
                    <td className="px-4 py-4">
                      <span className="rounded-full bg-blue-500/10 px-2.5 py-1 text-xs capitalize text-blue-300">
                        {user.plan}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-right font-semibold text-amber-400">{number.format(user.balance)}</td>
                    <td className="px-4 py-4 text-right text-blue-300">{number.format(user.includedRemaining)}</td>
                    <td className="px-4 py-4 text-right text-violet-400">{number.format(user.bonusBalance)}</td>
                    <td className="px-4 py-4 text-right text-rose-400">{number.format(user.usedThisMonth)}</td>
                    <td className="px-4 py-4 text-right text-white/55">{number.format(user.totalTokens)}</td>
                    <td className="px-5 py-4">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => router.push(`/users/${user.id}`)}
                          title="Voir l’historique"
                          className="rounded-lg bg-white/5 p-2 text-white/50 transition hover:bg-white/10 hover:text-white"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => openGrant(user, 'promotion')}
                          className="flex items-center gap-1.5 rounded-lg bg-violet-500/15 px-3 py-2 text-xs font-semibold text-violet-300 transition hover:bg-violet-500/25"
                        >
                          <Gift className="h-4 w-4" /> Promo
                        </button>
                        <button
                          onClick={() => openGrant(user, 'manual')}
                          className="flex items-center gap-1.5 rounded-lg bg-sala-primary px-3 py-2 text-xs font-semibold text-white transition hover:bg-blue-500"
                        >
                          <Plus className="h-4 w-4" /> Ajouter
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-3xl border border-white/10 bg-[#0b1020] p-6 shadow-2xl">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/35">
                  {grantType === 'promotion' ? 'Campagne promotionnelle' : 'Ajustement manuel'}
                </p>
                <h2 className="mt-1 text-xl font-bold text-white">Ajouter des crédits</h2>
                <p className="mt-1 text-sm text-white/45">{selectedUser.email}</p>
              </div>
              <button onClick={closeModal} className="rounded-lg p-2 text-white/35 hover:bg-white/5 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setGrantType('manual')}
                className={`rounded-xl border p-3 text-left transition ${grantType === 'manual' ? 'border-blue-500/60 bg-blue-500/10' : 'border-white/10 bg-white/[0.02]'}`}
              >
                <Coins className="mb-2 h-5 w-5 text-blue-400" />
                <p className="text-sm font-semibold text-white">Ajout manuel</p>
                <p className="mt-1 text-xs text-white/35">Support ou geste commercial</p>
              </button>
              <button
                type="button"
                onClick={() => {
                  setGrantType('promotion')
                  if (!description) setDescription('Bonus promotionnel de bienvenue')
                }}
                className={`rounded-xl border p-3 text-left transition ${grantType === 'promotion' ? 'border-violet-500/60 bg-violet-500/10' : 'border-white/10 bg-white/[0.02]'}`}
              >
                <Sparkles className="mb-2 h-5 w-5 text-violet-400" />
                <p className="text-sm font-semibold text-white">Promotion</p>
                <p className="mt-1 text-xs text-white/35">Bonus nouveau client</p>
              </button>
            </div>

            <form onSubmit={handleAddCredits} className="mt-5 space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-white/75">Nombre de crédits</label>
                <input
                  type="number"
                  min="1"
                  max="1000000"
                  value={creditsToAdd}
                  onChange={event => setCreditsToAdd(event.target.value)}
                  placeholder="Ex. 100"
                  autoFocus
                  required
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none placeholder:text-white/20 focus:border-blue-500/60"
                />
                <div className="mt-2 flex gap-2">
                  {[50, 100, 250, 500].map(preset => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => setCreditsToAdd(String(preset))}
                      className="rounded-lg bg-white/5 px-3 py-1.5 text-xs text-white/50 hover:bg-white/10 hover:text-white"
                    >
                      +{preset}
                    </button>
                  ))}
                </div>
                <p className="mt-2 text-xs text-white/35">
                  Solde actuel : {number.format(selectedUser.balance)} · 1 crédit = 1 000 tokens
                </p>
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-white/75">Motif</label>
                <input
                  value={description}
                  onChange={event => setDescription(event.target.value)}
                  maxLength={500}
                  placeholder="Ex. Bonus de lancement juillet"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none placeholder:text-white/20 focus:border-blue-500/60"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={closeModal} disabled={submitting} className="flex-1 rounded-xl bg-white/5 px-4 py-3 text-sm font-semibold text-white/65 hover:bg-white/10">
                  Annuler
                </button>
                <button type="submit" disabled={submitting || !creditsToAdd} className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-sala-primary px-4 py-3 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50">
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : grantType === 'promotion' ? <Gift className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                  Confirmer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
