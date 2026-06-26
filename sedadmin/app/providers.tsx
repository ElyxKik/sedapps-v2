'use client'

import { useEffect, useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    
    // Get theme from localStorage — default to dark (admin dashboard is dark-first)
    const storedTheme = localStorage.getItem('theme')
    const isDark = storedTheme !== 'light' // default dark unless explicitly light

    // Apply theme
    const html = document.documentElement
    if (isDark) {
      html.classList.add('dark')
      html.style.colorScheme = 'dark'
    } else {
      html.classList.remove('dark')
      html.style.colorScheme = 'light'
    }
  }, [])

  // Prevent hydration mismatch
  if (!mounted) return <>{children}</>

  return <>{children}</>
}
