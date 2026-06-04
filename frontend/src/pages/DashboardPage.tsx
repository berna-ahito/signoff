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

const urgencyClass: Record<string, string> = {
  low: '',
  medium: '',
  high: 'urgency-high',
  critical: 'urgency-critical',
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

  useEffect(() => {
    listRequests()
      .then(setRequests)
      .catch(() => setError('Failed to load requests.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="loading-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" /> Loading requests…
      </div>
    )
  }

  if (error) {
    return <div className="alert alert-error" role="alert">{error}</div>
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2 className="page-title">Purchase Requests</h2>
          <p className="page-subtitle">
            {role === 'requester' ? 'Your submitted requests' : 'Requests assigned for your review'}
          </p>
        </div>
        {role === 'requester' && (
          <button className="btn btn-primary" onClick={() => navigate('/submit')} aria-label="Create new purchase request">
            + New Request
          </button>
        )}
      </div>

      <div className="card">
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
                    style={{ cursor: 'pointer' }}
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && navigate(`/requests/${req.id}`)}
                    aria-label={`View request: ${req.title}`}
                    role="button"
                  >
                    <td>
                      <span className="truncate" style={{ display: 'block', maxWidth: 280 }}>
                        {req.title}
                      </span>
                    </td>
                    <td className="text-muted">{req.category}</td>
                    <td>
                      <span className={urgencyClass[req.urgency]}>
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
