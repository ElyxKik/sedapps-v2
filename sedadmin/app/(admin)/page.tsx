import { supabaseAdmin } from '@/lib/supabase'
import { Users, FolderKanban, Globe, CreditCard, TrendingUp, Activity } from 'lucide-react'

async function getStats() {
  const [users, projects, domains, subs] = await Promise.all([
    supabaseAdmin.from('users').select('id, created_at', { count: 'exact' }),
    supabaseAdmin.from('projects').select('id, created_at, status', { count: 'exact' }),
    supabaseAdmin.from('domains').select('id', { count: 'exact' }),
    supabaseAdmin.from('subscriptions').select('id, status', { count: 'exact' }),
  ])

  const now = new Date()
  const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
  const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1)

  const newUsersThisMonth = (users.data ?? []).filter((u: { id: string; created_at: string }) =>
    new Date(u.created_at) >= thisMonth
  ).length
  const newUsersLastMonth = (users.data ?? []).filter((u: { id: string; created_at: string }) => {
    const d = new Date(u.created_at)
    return d >= lastMonth && d < thisMonth
  }).length

  return {
    totalUsers: users.count ?? 0,
    totalProjects: projects.count ?? 0,
    totalDomains: (domains as any).count ?? 0,
    totalSubs: (subs as any).count ?? 0,
    newUsersThisMonth,
    userGrowth: newUsersLastMonth > 0
      ? Math.round(((newUsersThisMonth - newUsersLastMonth) / newUsersLastMonth) * 100)
      : 0,
    recentUsers: (users.data ?? []).slice(-5).reverse(),
    recentProjects: (projects.data ?? []).slice(-5).reverse(),
  }
}

function StatCard({ label, value, sub, icon: Icon, color }: {
  label: string; value: number | string; sub?: string; icon: any; color: string
}) {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      <p className="text-3xl font-bold text-white">{value}</p>
      <p className="text-sm text-white/50 mt-1">{label}</p>
      {sub && <p className="text-xs text-emerald-400 mt-2">{sub}</p>}
    </div>
  )
}

export default async function DashboardPage() {
  const stats = await getStats()

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Vue d'ensemble</h1>
        <p className="text-white/40 text-sm mt-1">Tableau de bord administrateur SedApps</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Utilisateurs total"
          value={stats.totalUsers}
          sub={`+${stats.newUsersThisMonth} ce mois`}
          icon={Users}
          color="bg-blue-600"
        />
        <StatCard
          label="Projets"
          value={stats.totalProjects}
          icon={FolderKanban}
          color="bg-violet-600"
        />
        <StatCard
          label="Domaines"
          value={stats.totalDomains}
          icon={Globe}
          color="bg-emerald-600"
        />
        <StatCard
          label="Abonnements actifs"
          value={stats.totalSubs}
          icon={CreditCard}
          color="bg-orange-600"
        />
      </div>

      {/* Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent users */}
        <div className="glass rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-400" />
              Derniers inscrits
            </h2>
            <a href="/users" className="text-xs text-violet-400 hover:text-violet-300">Voir tout →</a>
          </div>
          <div className="space-y-2">
            {stats.recentUsers.length === 0 && <p className="text-white/30 text-xs">Aucun utilisateur</p>}
            {stats.recentUsers.map((u: any) => (
              <div key={u.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-violet-600/30 flex items-center justify-center text-xs text-violet-300 font-bold">
                    {u.id?.slice(0, 1).toUpperCase()}
                  </div>
                  <span className="text-xs text-white/70 font-mono">{u.id?.slice(0, 12)}…</span>
                </div>
                <span className="text-xs text-white/30">{new Date(u.created_at).toLocaleDateString('fr')}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent projects */}
        <div className="glass rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <FolderKanban className="w-4 h-4 text-violet-400" />
              Derniers projets
            </h2>
            <a href="/projects" className="text-xs text-violet-400 hover:text-violet-300">Voir tout →</a>
          </div>
          <div className="space-y-2">
            {stats.recentProjects.length === 0 && <p className="text-white/30 text-xs">Aucun projet</p>}
            {stats.recentProjects.map((p: any) => (
              <div key={p.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                <span className="text-xs text-white/70 font-mono">{p.id?.slice(0, 16)}…</span>
                <span className={`badge ${p.status === 'live' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-white/5 text-white/30'}`}>
                  {p.status ?? 'draft'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
