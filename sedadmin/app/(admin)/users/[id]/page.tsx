'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  ArrowLeft, Mail, Calendar, Clock, Activity, CreditCard,
  FolderKanban, Globe, ExternalLink, Ban, CheckCircle,
  Trash2, Loader2, ShieldCheck, ShieldOff, RefreshCw, Eye, Code2, Zap,
  TrendingDown, TrendingUp,
} from 'lucide-react'

const MAIN_APP = process.env.NEXT_PUBLIC_MAIN_APP_URL || 'http://localhost:3000'

interface CreditTransaction {
  id: string
  type: 'purchase' | 'consumption' | 'refund' | 'bonus'
  credits_delta: number
  balance_after: number
  generation_type?: string
  tokens_used?: number
  llm_cost_usd?: number
  description?: string
  created_at: string
}

interface CreditData {
  balance: number
  total_purchased: number
  total_consumed: number
}

interface UserDetail {
  user: {
    id: string
    email: string
    created_at: string
    last_sign_in_at?: string
    banned_until?: string
    email_confirmed_at?: string
    user_metadata?: { full_name?: string; avatar_url?: string }
  }
  projects: {
    id: string
    name: string
    slug: string
    domain?: string
    stack_type: string
    status: string
    visits: number
    created_at: string
  }[]
  subscriptions: {
    id: string
    plan: string
    status: string
    current_period_end?: string
    cancel_at_period_end?: boolean
    stripe_subscription_id?: string
    stripe_customer_id?: string
    created_at: string
  }[]
  domains: {
    id: string
    domain: string
    verified: boolean
    created_at: string
  }[]
}

const STATUS_COLORS: Record<string, string> = {
  active:   'bg-emerald-500/15 text-emerald-400',
  trialing: 'bg-blue-500/15 text-blue-400',
  past_due: 'bg-yellow-500/15 text-yellow-400',
  canceled: 'bg-red-500/15 text-red-400',
  live:     'bg-emerald-500/15 text-emerald-400',
  draft:    'bg-white/8 text-white/40',
}

const STACK_ICONS: Record<string, string> = { wordpress: '📝', code: '🌐' }

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="glass rounded-2xl p-5">
      <h2 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
        {icon}{title}
      </h2>
      {children}
    </div>
  )
}

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [data, setData] = useState<UserDetail | null>(null)
  const [credits, setCredits] = useState<{ balance: CreditData; transactions: CreditTransaction[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState('')

  const fetchDetail = async () => {
    setLoading(true)
    const [userRes, creditsRes] = await Promise.all([
      fetch(`/api/users/${id}`),
      fetch(`/api/users/${id}/credits`),
    ])
    const userJson = await userRes.json()
    const creditsJson = await creditsRes.json()
    setData(userJson)
    setCredits(creditsJson)
    setLoading(false)
  }

  useEffect(() => { fetchDetail() }, [id])

  const isBanned = (u: UserDetail['user']) =>
    !!u.banned_until && new Date(u.banned_until) > new Date()

  const handleBan = async (ban: boolean) => {
    if (!data) return
    setActionLoading('ban')
    await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: ban ? 'ban' : 'unban', userId: id }),
    })
    await fetchDetail()
    setActionLoading('')
  }

  const handleDelete = async () => {
    if (!data || !confirm('Supprimer définitivement cet utilisateur ?')) return
    setActionLoading('delete')
    await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'delete', userId: id }),
    })
    router.push('/users')
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center gap-2 text-white/40">
        <Loader2 className="w-4 h-4 animate-spin" /> Chargement…
      </div>
    )
  }

  if (!data?.user) {
    return (
      <div className="p-8">
        <p className="text-white/40">Utilisateur introuvable.</p>
        <button onClick={() => router.push('/users')} className="mt-4 text-violet-400 text-sm hover:underline">
          ← Retour
        </button>
      </div>
    )
  }

  const { user, projects, subscriptions, domains } = data
  const activeSub = subscriptions.find(s => s.status === 'active' || s.status === 'trialing')
  const displayName = user.user_metadata?.full_name || user.email?.split('@')[0] || '—'

  return (
    <div className="p-8 max-w-4xl">
      {/* Back + header */}
      <button
        onClick={() => router.push('/users')}
        className="flex items-center gap-2 text-white/40 hover:text-white text-sm mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Retour aux utilisateurs
      </button>

      {/* User header */}
      <div className="glass rounded-2xl p-6 mb-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600/50 to-blue-600/50 flex items-center justify-center text-2xl font-bold text-white/80 flex-shrink-0">
              {user.email?.[0]?.toUpperCase()}
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">{displayName}</h1>
              <p className="text-white/40 text-sm">{user.email}</p>
              <div className="flex items-center gap-2 mt-2">
                {isBanned(user)
                  ? <span className="badge bg-red-500/15 text-red-400">Banni</span>
                  : user.email_confirmed_at
                    ? <span className="badge bg-emerald-500/15 text-emerald-400">Actif</span>
                    : <span className="badge bg-yellow-500/15 text-yellow-400">Non vérifié</span>}
                {activeSub && (
                  <span className="badge bg-violet-500/15 text-violet-300 capitalize">{activeSub.plan}</span>
                )}
              </div>
            </div>
          </div>
          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={fetchDetail}
              className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/40 hover:text-white transition-colors"
              title="Actualiser"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleBan(!isBanned(user))}
              disabled={actionLoading === 'ban'}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
                isBanned(user)
                  ? 'bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30'
                  : 'bg-orange-600/20 text-orange-400 hover:bg-orange-600/30'
              }`}
            >
              {actionLoading === 'ban'
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : isBanned(user) ? <ShieldCheck className="w-4 h-4" /> : <ShieldOff className="w-4 h-4" />}
              {isBanned(user) ? 'Débannir' : 'Bannir'}
            </button>
            <button
              onClick={handleDelete}
              disabled={actionLoading === 'delete'}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-red-600/20 text-red-400 hover:bg-red-600/30 transition-colors"
            >
              {actionLoading === 'delete' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
              Supprimer
            </button>
          </div>
        </div>

        {/* Meta infos */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5 pt-5 border-t border-white/8">
          <div>
            <p className="text-white/30 text-xs mb-1 flex items-center gap-1"><Calendar className="w-3 h-3" /> Inscrit le</p>
            <p className="text-white/80 text-sm font-medium">
              {new Date(user.created_at).toLocaleDateString('fr', { day: 'numeric', month: 'long', year: 'numeric' })}
            </p>
          </div>
          {user.last_sign_in_at && (
            <div>
              <p className="text-white/30 text-xs mb-1 flex items-center gap-1"><Clock className="w-3 h-3" /> Dernière connexion</p>
              <p className="text-white/80 text-sm font-medium">
                {new Date(user.last_sign_in_at).toLocaleDateString('fr', { day: 'numeric', month: 'short', year: 'numeric' })}
              </p>
            </div>
          )}
          <div>
            <p className="text-white/30 text-xs mb-1 flex items-center gap-1"><FolderKanban className="w-3 h-3" /> Projets</p>
            <p className="text-white/80 text-sm font-medium">{projects.length}</p>
          </div>
          <div>
            <p className="text-white/30 text-xs mb-1 flex items-center gap-1"><Activity className="w-3 h-3" /> ID</p>
            <p className="text-white/40 text-xs font-mono truncate">{user.id}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Crédits */}
        <Section icon={<Zap className="w-4 h-4 text-amber-400" />} title="Consommation de Crédits">
          {!credits ? (
            <p className="text-white/30 text-sm">Chargement des crédits…</p>
          ) : (
            <div className="space-y-4">
              {/* Stats cards */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-white/5 rounded-xl p-3 text-center">
                  <p className="text-white/40 text-xs mb-1">Solde</p>
                  <p className="text-amber-400 font-bold text-lg">{credits.balance.balance.toLocaleString()}</p>
                </div>
                <div className="bg-emerald-500/10 rounded-xl p-3 text-center border border-emerald-500/20">
                  <p className="text-emerald-400/60 text-xs mb-1 flex items-center justify-center gap-1">
                    <TrendingUp className="w-3 h-3" /> Acheté
                  </p>
                  <p className="text-emerald-400 font-bold text-lg">{credits.balance.total_purchased.toLocaleString()}</p>
                </div>
                <div className="bg-red-500/10 rounded-xl p-3 text-center border border-red-500/20">
                  <p className="text-red-400/60 text-xs mb-1 flex items-center justify-center gap-1">
                    <TrendingDown className="w-3 h-3" /> Consommé
                  </p>
                  <p className="text-red-400 font-bold text-lg">{credits.balance.total_consumed.toLocaleString()}</p>
                </div>
              </div>

              {/* Progress bar */}
              {credits.balance.total_purchased > 0 && (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-white/40 text-xs">Utilisation</p>
                    <p className="text-white/60 text-xs">
                      {Math.round((credits.balance.total_consumed / credits.balance.total_purchased) * 100)}%
                    </p>
                  </div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-amber-500 to-orange-500"
                      style={{
                        width: `${Math.min(
                          (credits.balance.total_consumed / credits.balance.total_purchased) * 100,
                          100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Transactions */}
              {credits.transactions.length > 0 && (
                <div className="pt-2 border-t border-white/8">
                  <p className="text-white/40 text-xs mb-3 font-semibold">Historique récent</p>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {credits.transactions.slice(0, 5).map(tx => (
                      <div key={tx.id} className="flex items-start gap-2 p-2 bg-white/[0.02] rounded-lg text-xs">
                        <div className="mt-0.5">
                          {tx.type === 'consumption' ? (
                            <TrendingDown className="w-3 h-3 text-red-400" />
                          ) : tx.type === 'purchase' ? (
                            <TrendingUp className="w-3 h-3 text-green-400" />
                          ) : (
                            <Zap className="w-3 h-3 text-blue-400" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between gap-2">
                            <p className="text-white/70 truncate">
                              {tx.type === 'consumption'
                                ? `Génération ${tx.generation_type?.replace('_', ' ') ?? 'site'}`
                                : tx.type === 'purchase'
                                ? 'Achat'
                                : tx.type === 'refund'
                                ? 'Remboursement'
                                : 'Bonus'}
                            </p>
                            <span className={`font-semibold flex-shrink-0 ${
                              tx.credits_delta > 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {tx.credits_delta > 0 ? '+' : ''}{tx.credits_delta}
                            </span>
                          </div>
                          {tx.tokens_used && (
                            <p className="text-white/30 text-[10px]">{tx.tokens_used.toLocaleString()} tokens</p>
                          )}
                          <p className="text-white/20 text-[10px]">
                            {new Date(tx.created_at).toLocaleDateString('fr', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Section>

        {/* Abonnements */}
        <Section icon={<CreditCard className="w-4 h-4 text-orange-400" />} title="Abonnements">
          {subscriptions.length === 0 ? (
            <p className="text-white/30 text-sm">Aucun abonnement — plan gratuit</p>
          ) : (
            <div className="space-y-3">
              {subscriptions.map(s => (
                <div key={s.id} className="border border-white/8 rounded-xl p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-white font-semibold capitalize">{s.plan}</span>
                    <span className={`badge ${STATUS_COLORS[s.status] ?? 'bg-white/8 text-white/40'}`}>
                      {s.status}{s.cancel_at_period_end ? ' (annulation prévue)' : ''}
                    </span>
                  </div>
                  {s.current_period_end && (
                    <p className="text-white/40 text-xs">
                      Renouvellement : {new Date(s.current_period_end).toLocaleDateString('fr')}
                    </p>
                  )}
                  <p className="text-white/25 text-xs">
                    Depuis le {new Date(s.created_at).toLocaleDateString('fr')}
                  </p>
                  <div className="flex gap-3 pt-1">
                    {s.stripe_subscription_id && (
                      <a href={`https://dashboard.stripe.com/subscriptions/${s.stripe_subscription_id}`}
                        target="_blank" rel="noopener noreferrer"
                        className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1">
                        Abonnement Stripe <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                    {s.stripe_customer_id && (
                      <a href={`https://dashboard.stripe.com/customers/${s.stripe_customer_id}`}
                        target="_blank" rel="noopener noreferrer"
                        className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                        Client Stripe <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* Projets */}
        <Section icon={<FolderKanban className="w-4 h-4 text-violet-400" />} title={`Projets (${projects.length})`}>
          {projects.length === 0 ? (
            <p className="text-white/30 text-sm">Aucun projet créé</p>
          ) : (
            <div className="space-y-2">
              {projects.map(p => (
                <div key={p.id} className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
                  <span className="text-lg flex-shrink-0">{STACK_ICONS[p.stack_type] ?? '🌐'}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-white/80 text-sm font-medium truncate">{p.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-white/30 text-xs">{p.visits ?? 0} visites</span>
                      <span className="text-white/20 text-xs">·</span>
                      <span className="text-white/30 text-xs">{new Date(p.created_at).toLocaleDateString('fr')}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={`badge text-xs ${STATUS_COLORS[p.status] ?? 'bg-white/8 text-white/30'}`}>{p.status}</span>
                    <a
                      href={`${MAIN_APP}/api/projects/${p.id}/preview/index.html`}
                      target="_blank" rel="noopener noreferrer"
                      className="text-white/25 hover:text-emerald-400 transition-colors"
                      title="Prévisualiser">
                      <Eye className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* Domaines */}
        <Section icon={<Globe className="w-4 h-4 text-emerald-400" />} title={`Domaines (${domains.length})`}>
          {domains.length === 0 ? (
            <p className="text-white/30 text-sm">Aucun domaine configuré</p>
          ) : (
            <div className="space-y-2">
              {domains.map(d => (
                <div key={d.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                  <div className="flex items-center gap-2">
                    <Globe className="w-3.5 h-3.5 text-white/25" />
                    <span className="text-white/70 text-sm">{d.domain}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`badge text-xs ${d.verified ? 'bg-emerald-500/15 text-emerald-400' : 'bg-yellow-500/15 text-yellow-400'}`}>
                      {d.verified ? 'Vérifié' : 'En attente'}
                    </span>
                    <a href={`https://${d.domain}`} target="_blank" rel="noopener noreferrer"
                      className="text-white/25 hover:text-blue-400 transition-colors">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* Email & auth */}
        <Section icon={<Mail className="w-4 h-4 text-blue-400" />} title="Informations du compte">
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-white/40">Email</span>
              <span className="text-white/80">{user.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/40">Email vérifié</span>
              <span className={user.email_confirmed_at ? 'text-emerald-400' : 'text-yellow-400'}>
                {user.email_confirmed_at
                  ? new Date(user.email_confirmed_at).toLocaleDateString('fr')
                  : 'Non vérifié'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/40">Statut ban</span>
              <span className={isBanned(user) ? 'text-red-400' : 'text-emerald-400'}>
                {isBanned(user)
                  ? `Banni jusqu'au ${new Date(user.banned_until!).toLocaleDateString('fr')}`
                  : 'Actif'}
              </span>
            </div>
            <div className="pt-2 border-t border-white/8">
              <p className="text-white/30 text-xs mb-1">UUID</p>
              <p className="text-white/40 text-xs font-mono break-all">{user.id}</p>
            </div>
          </div>
        </Section>
      </div>
    </div>
  )
}
