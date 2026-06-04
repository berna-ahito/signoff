import { useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { BrandMark } from './BrandMark'
import type { Role } from '../types'

interface Props {
  role: Role | null
  onLogout: () => void
  pageTitle: string
  children: React.ReactNode
}

const roleLabel: Record<Role, string> = {
  requester: 'Requester',
  manager: 'Manager',
  finance: 'Finance',
  admin: 'Admin',
}

export function Layout({ role, onLogout, pageTitle, children }: Props) {
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  function handleLogout() {
    onLogout()
    navigate('/login')
  }

  function closeNav() {
    setSidebarOpen(false)
  }

  return (
    <div className="layout">
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={closeNav} aria-hidden="true" />
      )}

      <nav
        id="main-nav"
        className={`sidebar${sidebarOpen ? ' sidebar-open' : ''}`}
        aria-label="Main navigation"
      >
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <BrandMark size={22} accentColor="#93c5fd" />
            <span>Procure<span className="logo-flow">Flow</span></span>
            <span className="logo-ai">AI</span>
          </div>
        </div>

        <div className="sidebar-nav">
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            aria-current={location.pathname === '/dashboard' ? 'page' : undefined}
            onClick={closeNav}
          >
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
              <path d="M2 3.5A1.5 1.5 0 013.5 2h3A1.5 1.5 0 018 3.5v3A1.5 1.5 0 016.5 8h-3A1.5 1.5 0 012 6.5v-3zm5.5 0A1.5 1.5 0 019 2h3a1.5 1.5 0 011.5 1.5v3A1.5 1.5 0 0112 8H9a1.5 1.5 0 01-1.5-1.5v-3zM2 9a1.5 1.5 0 011.5-1.5h3A1.5 1.5 0 018 9v3a1.5 1.5 0 01-1.5 1.5h-3A1.5 1.5 0 012 12V9zm5.5 0A1.5 1.5 0 019 7.5h3A1.5 1.5 0 0113.5 9v3A1.5 1.5 0 0112 13.5H9A1.5 1.5 0 017.5 12V9z" fill="currentColor" />
            </svg>
            Dashboard
          </NavLink>

          {role === 'requester' && (
            <NavLink
              to="/submit"
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
              aria-current={location.pathname === '/submit' ? 'page' : undefined}
              onClick={closeNav}
            >
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
                <path d="M7.5 1a6.5 6.5 0 100 13A6.5 6.5 0 007.5 1zM7 4.5a.5.5 0 011 0V7h2.5a.5.5 0 010 1H8v2.5a.5.5 0 01-1 0V8H4.5a.5.5 0 010-1H7V4.5z" fill="currentColor" />
              </svg>
              New Request
            </NavLink>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-role-chip">
            {role ? roleLabel[role] : '—'}
          </div>
          <button
            className="btn btn-ghost"
            style={{ width: '100%', justifyContent: 'flex-start', fontSize: 13 }}
            onClick={handleLogout}
          >
            Sign out
          </button>
        </div>
      </nav>

      <div className="main-content">
        <header className="topbar">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen((o) => !o)}
            aria-label={sidebarOpen ? 'Close navigation' : 'Open navigation'}
            aria-expanded={sidebarOpen}
            aria-controls="main-nav"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path d="M2 4.5h14M2 9h14M2 13.5h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
          <h1 className="topbar-title">{pageTitle}</h1>
        </header>
        <main className="page-content">
          {children}
        </main>
      </div>
    </div>
  )
}
