import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Layout } from './components/Layout'
import { useAuth } from './hooks/useAuth'
import { AuditPage } from './pages/AuditPage'
import { DashboardPage } from './pages/DashboardPage'
import { DetailPage } from './pages/DetailPage'
import { LoginPage } from './pages/LoginPage'
import { SubmitPage } from './pages/SubmitPage'
import { UserManagementPage } from './pages/UserManagementPage'

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/submit': 'New Request',
  '/audit': 'Audit Log',
  '/users': 'User Management',
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
  const { isAuthenticated, role, login, logout } = useAuth()
  const location = useLocation()

  const pageTitle =
    PAGE_TITLES[location.pathname] ??
    (location.pathname.startsWith('/requests/') ? 'Request Detail' : 'ProcureFlow AI')

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage onLogin={login} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <Layout role={role} onLogout={logout} pageTitle={pageTitle}>
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
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  )
}
