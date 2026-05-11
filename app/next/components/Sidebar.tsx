'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  PenTool, 
  CheckCircle, 
  History, 
  Menu, 
  X, 
  Home,
  LogOut,
  User
} from 'lucide-react'
import { useUser } from '@/lib/hooks'

interface SidebarProps {
  children: React.ReactNode
}

export function Sidebar({ children }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()
  const { user } = useUser()

  // Close sidebar when route changes on mobile
  useEffect(() => {
    setIsOpen(false)
  }, [pathname])

  const navItems = [
    {
      name: 'Generate Content',
      href: '/',
      icon: Home,
      exact: true
    },
    {
      name: 'Generate Content',
      href: '/dashboard',
      icon: PenTool,
      exact: false
    },
    {
      name: 'Approval Queue',
      href: '/approvals',
      icon: CheckCircle,
      exact: false
    },
    {
      name: 'History',
      href: '/history',
      icon: History,
      exact: false
    }
  ]

  const isActive = (href: string, exact: boolean) => {
    if (exact) {
      return pathname === href
    }
    return pathname.startsWith(href)
  }

  const NavLink = ({ item }: { item: typeof navItems[0] }) => {
    const active = isActive(item.href, item.exact)
    const Icon = item.icon

    return (
      <Link
        href={item.href}
        className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
          active 
            ? 'bg-indigo-50 text-indigo-700 font-semibold' 
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        }`}
      >
        <Icon 
          className={`w-5 h-5 flex-shrink-0 ${
            active ? 'text-indigo-600' : 'text-gray-500 group-hover:text-gray-700'
          }`}
        />
        <span className="text-sm">{item.name}</span>
      </Link>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-40 flex items-center justify-between px-4">
        <Link href="/" className="flex items-center space-x-2">
          <PenTool className="w-6 h-6 text-indigo-600" />
          <span className="font-bold text-gray-900">InsightForge</span>
        </Link>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
        >
          {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-200 z-50 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-full flex flex-col">
          {/* Logo */}
          <div className="h-16 flex items-center px-6 border-b border-gray-200">
            <Link href="/" className="flex items-center space-x-2">
              <PenTool className="w-6 h-6 text-indigo-600" />
              <span className="font-bold text-gray-900 text-lg">InsightForge</span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            <div className="pb-4">
              <h3 className="px-4 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Navigation
              </h3>
              <div className="space-y-1">
                {navItems
                  .filter(item => {
                    // For root '/', show only when at root
                    if (item.exact && item.href === '/') {
                      return pathname === '/'
                    }
                    // For '/dashboard', don't show when at root '/'
                    if (!item.exact && item.href === '/dashboard') {
                      return pathname !== '/'
                    }
                    return true
                  })
                  .map((item, index) => (
                    <NavLink key={`${item.href}-${index}`} item={item} />
                  ))}
              </div>
            </div>
          </nav>

          {/* User Profile */}
          <div className="p-4 border-t border-gray-200">
            {user ? (
              <div className="space-y-3">
                <div className="flex items-center space-x-3 px-3 py-2">
                  <div className="w-9 h-9 bg-indigo-100 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {user.full_name || user.email.split('@')[0]}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {user.email}
                    </p>
                  </div>
                </div>
                <button
                  onClick={async () => {
                    const { supabase } = await import('@/lib/supabase/client')
                    await supabase.auth.signOut()
                    window.location.href = '/login'
                  }}
                  className="w-full flex items-center space-x-3 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors text-sm"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Sign out</span>
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="w-full flex items-center space-x-3 px-3 py-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors text-sm"
              >
                <User className="w-5 h-5" />
                <span>Sign in</span>
              </Link>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="lg:ml-64 pt-16 lg:pt-0 min-h-screen">
        <div className="p-4 md:p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  )
}