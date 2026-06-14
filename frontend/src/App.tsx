import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Toaster } from 'sonner'
import { ErrorBoundary } from './components/ErrorBoundary'
import { Layout } from './components/Layout'
import { useAuth } from './hooks/useAuth'
import { AdminPage } from './pages/AdminPage'
import { AuditPage } from './pages/AuditPage'
import { DashboardPage } from './pages/DashboardPage'
import { DetailPage } from './pages/DetailPage'
import { LoginPage } from './pages/LoginPage'
import { RequestFormPage } from './pages/RequestFormPage'
import { RequestsPage } from './pages/RequestsPage'
import { SubmitPage } from './pages/SubmitPage'
import { UserManagementPage } from './pages/UserManagementPage'

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/submit': 'New Request',
  '/requests/new': 'New Request',
  '/requests': 'All Requests',
  '/audit': 'Audit Log',
  '/users': 'User Management',
  '/admin': 'Admin',
}

function LoadingScreen() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'var(--color-bg)',
        flexDirection: 'column',
        gap: 16,
      }}
    >
      <div
        style={{
          width: 200,
          height: 8,
          borderRadius: 4,
          background: 'var(--color-border)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: '40%',
            background: 'var(--color-primary)',
            borderRadius: 4,
            animation: 'shimmer 1.2s ease-in-out infinite',
          }}
        />
      </div>
      <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>Loading…</span>
    </div>
  )
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return <>{children}</>
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, role } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (role !== 'admin') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default function App() {
  const { isAuthenticated, role, login, logout, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <LoadingScreen />
  }

  const pageTitle =
    PAGE_TITLES[location.pathname] ??
    (location.pathname.endsWith('/edit')
      ? 'Edit Request'
      : location.pathname.startsWith('/requests/')
        ? 'Request Detail'
        : 'Signoff')

  if (!isAuthenticated) {
    return (
      <ErrorBoundary>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={login} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </ErrorBoundary>
    )
  }

  return (
    <Layout role={role} onLogout={logout} pageTitle={pageTitle}>
      <Toaster richColors position="top-right" />
      <ErrorBoundary>
      <Routes>
        <Route path="/login" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <DashboardPage role={role} />
            </RequireAuth>
          }
        />
        <Route
          path="/submit"
          element={
            <RequireAuth>
              <SubmitPage />
            </RequireAuth>
          }
        />
        <Route
          path="/requests"
          element={
            <RequireAuth>
              <RequestsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/requests/new"
          element={
            <RequireAuth>
              <RequestFormPage />
            </RequireAuth>
          }
        />
        <Route
          path="/requests/:id/edit"
          element={
            <RequireAuth>
              <RequestFormPage />
            </RequireAuth>
          }
        />
        <Route
          path="/requests/:id"
          element={
            <RequireAuth>
              <DetailPage role={role} />
            </RequireAuth>
          }
        />
        <Route
          path="/audit"
          element={
            <RequireAdmin>
              <AuditPage />
            </RequireAdmin>
          }
        />
        <Route
          path="/users"
          element={
            <RequireAdmin>
              <UserManagementPage />
            </RequireAdmin>
          }
        />
        <Route
          path="/admin"
          element={
            <RequireAdmin>
              <AdminPage />
            </RequireAdmin>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      </ErrorBoundary>
    </Layout>
  )
}
