'use client'

import Link from 'next/link'
import Image from 'next/image'
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
    <aside className="w-60 flex-shrink-0 flex flex-col h-screen bg-[#111118] border-r border-white/8 sticky top-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/8">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0 overflow-hidden">
            <Image
              src="/logo-sedapps.png"
              alt="Sedapps Logo"
              width={32}
              height={32}
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <p className="text-sm font-bold text-white">SedAdmin</p>
            <p className="text-[10px] text-white/30">Administration</p>
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
                  ? 'bg-violet-600/20 text-violet-300 border border-violet-500/20'
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
      <div className="p-3 border-t border-white/8 space-y-2">
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
