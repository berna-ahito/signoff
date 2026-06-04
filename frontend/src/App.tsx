import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Layout } from './components/Layout'
import { useAuth } from './hooks/useAuth'
import { DashboardPage } from './pages/DashboardPage'
import { DetailPage } from './pages/DetailPage'
import { LoginPage } from './pages/LoginPage'
import { SubmitPage } from './pages/SubmitPage'

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/submit': 'New Request',
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
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
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  )
}
