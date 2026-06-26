'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard, Users, CreditCard, Bot, FolderKanban,
  Globe, Settings, LogOut, Activity, Bell, Zap,
} from 'lucide-react'
import { ThemeToggle } from './ThemeToggle'

const NAV = [
  { label: 'Vue d\'ensemble', href: '/', icon: LayoutDashboard },
  { label: 'Utilisateurs', href: '/users', icon: Users },
  { label: 'Crédits', href: '/credits', icon: Zap },
  { label: 'Abonnements', href: '/subscriptions', icon: CreditCard },
  { label: 'Projets', href: '/projects', icon: FolderKanban },
  { label: 'Domaines', href: '/domains', icon: Globe },
  { label: 'IA / LLM', href: '/llm', icon: Bot },
  { label: 'Activité', href: '/activity', icon: Activity },
  { label: 'Notifications', href: '/notifications', icon: Bell },
  { label: 'Paramètres', href: '/settings', icon: Settings },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
  }

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col h-screen bg-sala-surface border-r border-white/6 sticky top-0">
      {/* Logo + Brand */}
      <div className="px-5 py-5 border-b border-white/6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-sala-primary/15 border border-sala-primary/20 flex items-center justify-center flex-shrink-0 overflow-hidden sala-glow">
            <img
              src="/logo-sala-ai.png"
              alt="Sala AI Logo"
              width={36}
              height={36}
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <p className="text-sm font-bold text-white tracking-tight">Sala AI</p>
            <p className="text-[10px] text-sala-primary/70 font-medium">Console Admin</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {NAV.map(({ label, href, icon: Icon }) => {
          const active = href === '/' ? pathname === '/' : pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                active
                  ? 'bg-sala-primary/15 text-sala-primary-light border border-sala-primary/20'
                  : 'text-white/50 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-white/6 space-y-2">
        <div className="flex gap-2">
          <ThemeToggle />
          <button
            onClick={handleLogout}
            className="flex-1 flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-white/40 hover:text-red-400 hover:bg-red-500/10 transition-all"
          >
            <LogOut className="w-4 h-4" />
            Déconnexion
          </button>
        </div>
      </div>
    </aside>
  )
}
