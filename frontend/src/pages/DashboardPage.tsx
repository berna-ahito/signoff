import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listRequests } from '../api/requests'
import { StatusBadge } from '../components/StatusBadge'
import type { RequestSummary, Role } from '../types'
import '../components/StatusBadge.css'

interface Props {
  role: Role | null
}

const urgencyLabel: Record<string, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  critical: 'Critical',
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function DashboardPage({ role }: Props) {
  const navigate = useNavigate()
  const [requests, setRequests] = useState<RequestSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    listRequests()
      .then(setRequests)
      .catch(() => setError('Failed to load requests.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="loading-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" /> Loading requests…
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div className="alert alert-error" role="alert">{error}</div>
        <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={load}>
          Retry
        </button>
      </div>
    )
  }

  const pendingCount = requests.filter((r) => r.status === 'pending_approval').length
  const approvedCount = requests.filter((r) => r.status === 'approved').length
  const totalValue = requests.reduce((sum, r) => sum + r.estimated_cost, 0)

  const draftCount = requests.filter((r) => r.status === 'draft').length
  const rejectedCount = requests.filter((r) => r.status === 'rejected').length

  return (
    <div className="workbench-shell">
      <div className="workbench-header">
        <div className="workbench-header-left">
          <div className="workbench-context">
            <span className="workbench-context-mark" aria-hidden="true" />
            <span className="workbench-context-label">Procurement Operations</span>
          </div>
          <h2 className="page-title">Procurement Workbench</h2>
          <p className="page-subtitle">
            {role === 'requester' ? 'Your submitted purchase requests' : 'Requests assigned for your review'}
          </p>
        </div>
        {role === 'requester' && (
          <button className="btn btn-primary" onClick={() => navigate('/submit')} aria-label="Create new purchase request">
            + New Request
          </button>
        )}
      </div>

      {requests.length > 0 && (
        <div className="stats-bar" aria-label="Summary statistics">
          <div className="stat-card" style={{ '--stat-accent': 'var(--color-text-subtle)' } as React.CSSProperties}>
            <div className="stat-label">Total Requests</div>
            <div className="stat-value">{requests.length}</div>
            <div className="stat-subtext">
              {draftCount > 0 ? `${draftCount} in draft` : 'all submitted'}
            </div>
          </div>
          <div className="stat-card" style={{ '--stat-accent': pendingCount > 0 ? 'var(--color-warning)' : 'var(--color-text-subtle)' } as React.CSSProperties}>
            <div className="stat-label">Awaiting Decision</div>
            <div className="stat-value" style={pendingCount > 0 ? { color: 'var(--color-warning)' } : {}}>
              {pendingCount}
            </div>
            <div className="stat-subtext">pending approval</div>
          </div>
          <div className="stat-card" style={{ '--stat-accent': approvedCount > 0 ? 'var(--color-success)' : 'var(--color-text-subtle)' } as React.CSSProperties}>
            <div className="stat-label">Approved</div>
            <div className="stat-value" style={approvedCount > 0 ? { color: 'var(--color-success)' } : {}}>
              {approvedCount}
            </div>
            <div className="stat-subtext">
              {rejectedCount > 0 ? `${rejectedCount} rejected` : 'no rejections'}
            </div>
          </div>
          <div className="stat-card" style={{ '--stat-accent': 'var(--color-ai)' } as React.CSSProperties}>
            <div className="stat-label">Pipeline Value</div>
            <div className="stat-value" style={{ fontSize: 20 }}>{formatCurrency(totalValue)}</div>
            <div className="stat-subtext">estimated spend</div>
          </div>
        </div>
      )}

      <div className="section-label" style={{ marginTop: requests.length > 0 ? 8 : 0 }}>
        Active Requests
      </div>

      <div className="card card-table">
        {requests.length === 0 ? (
          <div className="empty-state">
            <p>No requests found.</p>
            {role === 'requester' && (
              <button className="btn btn-primary" onClick={() => navigate('/submit')}>
                Create your first request
              </button>
            )}
          </div>
        ) : (
          <div className="table-wrap">
            <table aria-label="Purchase requests list">
              <thead>
                <tr>
                  <th scope="col">Title</th>
                  <th scope="col">Category</th>
                  <th scope="col">Urgency</th>
                  <th scope="col">Amount</th>
                  <th scope="col">Status</th>
                  <th scope="col">Submitted</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((req) => (
                  <tr
                    key={req.id}
                    onClick={() => navigate(`/requests/${req.id}`)}
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        navigate(`/requests/${req.id}`)
                      }
                    }}
                    aria-label={`View request: ${req.title}`}
                  >
                    <td>
                      <span className="truncate" style={{ display: 'block', maxWidth: 280 }}>
                        {req.title}
                      </span>
                    </td>
                    <td className="text-muted">{req.category}</td>
                    <td>
                      <span className={`urgency-pill urgency-${req.urgency}`}>
                        {urgencyLabel[req.urgency] ?? req.urgency}
                      </span>
                    </td>
                    <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                      {formatCurrency(req.estimated_cost)}
                    </td>
                    <td><StatusBadge status={req.status} /></td>
                    <td className="text-muted text-sm">{formatDate(req.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
