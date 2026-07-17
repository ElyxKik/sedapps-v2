import Link from 'next/link'
import {
  Activity,
  Bot,
  Coins,
  FolderKanban,
  Globe,
  TrendingDown,
  Users,
  Zap,
} from 'lucide-react'

import { backendRequest } from '@/lib/sedapps-backend'

export const dynamic = 'force-dynamic'

interface Overview {
  users: {
    total: number
    new_this_month: number
    new_last_month: number
    growth_percent: number | null
  }
  projects: { total: number }
  domains: { total: number; active: number }
  subscriptions: { active: number }
  credits: {
    available: number
    bonus: number
    used_this_month: number
    granted_total: number
    consumed_total: number
    tokens_total: number
  }
  jobs: { total: number; success: number; degraded: number; failed: number }
  recent_users: {
    id: string
    email: string
    name: string
    created_at: string
    is_active: boolean
  }[]
  recent_projects: {
    id: string
    name: string
    organization: string
    status: string
    created_at: string
  }[]
}

const formatter = new Intl.NumberFormat('fr-FR')

async function getOverview(): Promise<Overview> {
  return backendRequest('/v1/admin/overview')
}

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  color,
}: {
  label: string
  value: number | string
  sub?: string
  icon: typeof Users
  color: string
}) {
  return (
    <div className="glass rounded-2xl border border-white/5 p-5">
      <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded-xl ${color}`}>
        <Icon className="h-5 w-5 text-white" />
      </div>
      <p className="text-3xl font-bold text-white">{value}</p>
      <p className="mt-1 text-sm text-white/50">{label}</p>
      {sub && <p className="mt-2 text-xs text-white/35">{sub}</p>}
    </div>
  )
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

export default async function DashboardPage() {
  const stats = await getOverview()
  const completedJobs = stats.jobs.success + stats.jobs.degraded
  const successRate = stats.jobs.total
    ? Math.round((completedJobs / stats.jobs.total) * 100)
    : 0

  return (
    <div className="space-y-8 p-6 lg:p-8">
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-400">
          <Activity className="h-4 w-4" /> Données PostgreSQL en direct
        </div>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">Vue d’ensemble</h1>
        <p className="mt-1 text-sm text-white/40">
          Aucun chiffre de démonstration : utilisateurs, projets, domaines, jobs et tokens viennent du backend de production.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <StatCard
          label="Utilisateurs"
          value={formatter.format(stats.users.total)}
          sub={`${stats.users.new_this_month} inscription(s) ce mois`}
          icon={Users}
          color="bg-blue-600"
        />
        <StatCard
          label="Projets réels"
          value={formatter.format(stats.projects.total)}
          icon={FolderKanban}
          color="bg-sky-600"
        />
        <StatCard
          label="Domaines"
          value={formatter.format(stats.domains.total)}
          sub={`${stats.domains.active} actif(s)`}
          icon={Globe}
          color="bg-emerald-600"
        />
        <StatCard
          label="Jobs IA"
          value={formatter.format(stats.jobs.total)}
          sub={`${successRate}% terminés · ${stats.jobs.failed} échec(s)`}
          icon={Bot}
          color="bg-violet-600"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="glass rounded-2xl border border-amber-500/10 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-white/45">Crédits utilisables</p>
            <Coins className="h-5 w-5 text-amber-400" />
          </div>
          <p className="mt-3 text-3xl font-bold text-amber-400">
            {formatter.format(stats.credits.available)}
          </p>
          <p className="mt-2 text-xs text-white/35">
            Quotas de plan restants + {formatter.format(stats.credits.bonus)} crédit(s) réellement ajouté(s)
          </p>
        </div>
        <div className="glass rounded-2xl border border-rose-500/10 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-white/45">Consommés ce mois</p>
            <TrendingDown className="h-5 w-5 text-rose-400" />
          </div>
          <p className="mt-3 text-3xl font-bold text-rose-400">
            {formatter.format(stats.credits.used_this_month)}
          </p>
          <p className="mt-2 text-xs text-white/35">
            {formatter.format(stats.credits.consumed_total)} crédit(s) dans l’historique complet
          </p>
        </div>
        <div className="glass rounded-2xl border border-blue-500/10 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-white/45">Tokens IA mesurés</p>
            <Zap className="h-5 w-5 text-blue-400" />
          </div>
          <p className="mt-3 text-3xl font-bold text-blue-400">
            {formatter.format(stats.credits.tokens_total)}
          </p>
          <p className="mt-2 text-xs text-white/35">Entrée + sortie, issus des traitements réellement exécutés</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="glass rounded-2xl border border-white/5 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-white">
              <Users className="h-4 w-4 text-blue-400" /> Derniers inscrits
            </h2>
            <Link href="/users" className="text-xs text-blue-300 hover:text-sky-300">Voir tout →</Link>
          </div>
          <div className="space-y-1">
            {stats.recent_users.length === 0 && <p className="py-6 text-center text-xs text-white/30">Aucun utilisateur</p>}
            {stats.recent_users.map(user => (
              <Link
                href={`/users/${user.id}`}
                key={user.id}
                className="flex items-center justify-between rounded-xl border-b border-white/5 px-2 py-3 transition hover:bg-white/[0.03]"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500/15 text-xs font-bold text-blue-300">
                    {user.name.slice(0, 1).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-white/80">{user.name}</p>
                    <p className="truncate text-xs text-white/35">{user.email}</p>
                  </div>
                </div>
                <div className="ml-3 text-right">
                  <span className={`text-[11px] ${user.is_active ? 'text-emerald-400' : 'text-red-400'}`}>
                    {user.is_active ? 'Actif' : 'Suspendu'}
                  </span>
                  <p className="text-[10px] text-white/25">{formatDate(user.created_at)}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className="glass rounded-2xl border border-white/5 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-white">
              <FolderKanban className="h-4 w-4 text-sky-400" /> Derniers projets
            </h2>
            <Link href="/projects" className="text-xs text-blue-300 hover:text-sky-300">Voir tout →</Link>
          </div>
          <div className="space-y-1">
            {stats.recent_projects.length === 0 && <p className="py-6 text-center text-xs text-white/30">Aucun projet</p>}
            {stats.recent_projects.map(project => (
              <div key={project.id} className="flex items-center justify-between rounded-xl border-b border-white/5 px-2 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-white/80">{project.name}</p>
                  <p className="truncate text-xs text-white/35">{project.organization}</p>
                </div>
                <div className="ml-3 text-right">
                  <span className={`badge text-[10px] ${project.status === 'published' || project.status === 'ready' ? 'bg-emerald-500/15 text-emerald-400' : project.status === 'generating' ? 'bg-blue-500/15 text-blue-300' : 'bg-white/5 text-white/35'}`}>
                    {project.status}
                  </span>
                  <p className="mt-1 text-[10px] text-white/25">{formatDate(project.created_at)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
