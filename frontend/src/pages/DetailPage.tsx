import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getRequest, submitRequest } from '../api/requests'
import { AIReviewPanel } from '../components/AIReviewPanel'
import { ApprovalActions } from '../components/ApprovalActions'
import { StatusBadge } from '../components/StatusBadge'
import type { RequestDetail, Role } from '../types'
import '../components/StatusBadge.css'
import '../components/AIReviewPanel.css'
import '../components/ApprovalActions.css'
import './DetailPage.css'

interface Props {
  role: Role | null
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function DetailPage({ role }: Props) {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [request, setRequest] = useState<RequestDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const loadRequest = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const data = await getRequest(parseInt(id, 10))
      setRequest(data)
    } catch {
      setError('Request not found or access denied.')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { loadRequest() }, [loadRequest])

  async function handleSubmit() {
    if (!request) return
    setSubmitting(true)
    try {
      const updated = await submitRequest(request.id)
      setRequest(updated)
    } catch {
      setError('Failed to submit request.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" /> Loading request…
      </div>
    )
  }

  if (error || !request) {
    return (
      <div>
        <div className="alert alert-error" role="alert">{error ?? 'Request not found.'}</div>
        <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </div>
    )
  }

  return (
    <div className="detail-layout">
      <div className="detail-main">
        {/* Header */}
        <div className="page-header" style={{ marginBottom: 16 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')} aria-label="Back to dashboard">
            ← Back
          </button>
          <div className="row" style={{ gap: 8 }}>
            <StatusBadge status={request.status} />
            {request.status === 'draft' && role === 'requester' && (
              <button
                className="btn btn-primary btn-sm"
                onClick={handleSubmit}
                disabled={submitting}
                aria-busy={submitting}
              >
                {submitting ? <><span className="spinner" aria-hidden="true" /> Submitting…</> : 'Submit for Review'}
              </button>
            )}
          </div>
        </div>

        {/* Dossier reference header */}
        <div className="dossier-header">
          <div className="dossier-meta">
            <span className="dossier-ref">PR-{String(request.id).padStart(4, '0')}</span>
            <StatusBadge status={request.status} />
          </div>
          <div className="dossier-dates">
            <span className="dossier-date-label">Filed</span>
            <span className="dossier-date">{formatDate(request.created_at)}</span>
          </div>
        </div>

        {/* Title card */}
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-body">
            <h2 className="detail-title">{request.title}</h2>
            <p className="detail-description">{request.description}</p>
          </div>
        </div>

        {/* Meta */}
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header"><span className="card-title">Request Details</span></div>
          <div className="card-body">
            <div className="meta-grid">
              <div className="meta-item">
                <span className="meta-label">Category</span>
                <span className="meta-value">{request.category}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Urgency</span>
                <span className={`meta-value urgency-${request.urgency}`}>{request.urgency}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Quantity</span>
                <span className="meta-value">{request.quantity}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Estimated Cost</span>
                <span className="meta-value" style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>
                  {formatCurrency(request.estimated_cost)}
                </span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Assigned To</span>
                <span className="meta-value">{request.assigned_role ?? '—'}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Submitted</span>
                <span className="meta-value">{formatDate(request.created_at)}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Last Updated</span>
                <span className="meta-value">{formatDate(request.updated_at)}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Request ID</span>
                <span className="meta-value mono">#{request.id}</span>
              </div>
            </div>

            <hr className="divider" />

            <div className="meta-item">
              <span className="meta-label">Business Justification</span>
              <p className="meta-value" style={{ lineHeight: 1.6, marginTop: 4 }}>{request.justification}</p>
            </div>
          </div>
        </div>

        {/* Approval actions (approvers only) */}
        <ApprovalActions request={request} role={role} onDecision={loadRequest} />
      </div>

      {/* AI Review sidebar */}
      <aside className="detail-sidebar" aria-label="AI review panel">
        <AIReviewPanel requestId={request.id} />
      </aside>
    </div>
  )
}
