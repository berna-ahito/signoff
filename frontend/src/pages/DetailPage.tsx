import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'
import { motion } from 'motion/react'
import type { Variants } from 'motion/react'
import { getRequest, submitRequest } from '../api/requests'
import { listAttachments, downloadAttachmentBlob } from '../api/attachments'
import { getRequestAuditLogs } from '../api/audit'
import { AIReviewPanel } from '../components/AIReviewPanel'
import { ApprovalActions } from '../components/ApprovalActions'
import { StatusBadge } from '../components/StatusBadge'
import type { Attachment, AuditLog, RequestDetail, Role } from '../types'
import '../components/StatusBadge.css'
import '../components/AIReviewPanel.css'
import '../components/ApprovalActions.css'
import './DetailPage.css'

interface Props {
  role: Role | null
}

const STAGGER: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } }
const ITEM: Variants = {
  hidden: { opacity: 0, x: -10 },
  show: { opacity: 1, x: 0, transition: { duration: 0.22, ease: 'easeOut' } },
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

function formatDateShort(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function actionLabel(action: string): string {
  const map: Record<string, string> = {
    created: 'Request created',
    submitted: 'Submitted for review',
    approved: 'Approved',
    rejected: 'Rejected',
    needs_more_info: 'More info requested',
    ai_reviewed: 'AI review completed',
    attachment_uploaded: 'Attachment uploaded',
    status_changed: 'Status changed',
  }
  return map[action] ?? action.replace(/_/g, ' ')
}

export function DetailPage({ role }: Props) {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [request, setRequest] = useState<RequestDetail | null>(null)
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const loadRequest = useCallback(async () => {
    if (!id) return
    const rid = parseInt(id, 10)
    setLoading(true)
    setError(null)
    try {
      const [req, atts] = await Promise.all([
        getRequest(rid),
        listAttachments(rid).catch(() => [] as Attachment[]),
      ])
      setRequest(req)
      setAttachments(atts)

      if (role === 'admin') {
        getRequestAuditLogs(rid)
          .then(setAuditLogs)
          .catch(() => setAuditLogs([]))
      }
    } catch {
      setError('Request not found or access denied.')
    } finally {
      setLoading(false)
    }
  }, [id, role])

  useEffect(() => { void loadRequest() }, [loadRequest])

  async function handleSubmit() {
    if (!request) return
    setSubmitting(true)
    try {
      const updated = await submitRequest(request.id)
      setRequest(updated)
      toast.success('Submitted for review')
    } catch {
      toast.error('Failed to submit request.')
      setError('Failed to submit request.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDownload(att: Attachment) {
    try {
      const blob = await downloadAttachmentBlob(request!.id, att.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = att.filename
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Download failed')
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

  const canEdit = request.status === 'draft' && role === 'requester'

  return (
    <div className="detail-layout">
      <div className="detail-main">
        {/* Nav header */}
        <div className="page-header" style={{ marginBottom: 16 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate(-1)} aria-label="Go back">
            ← Back
          </button>
          <div className="row" style={{ gap: 8 }}>
            <StatusBadge status={request.status} />
            {canEdit && (
              <button
                className="btn btn-outline btn-sm"
                onClick={() => navigate(`/requests/${request.id}/edit`)}
              >
                Edit Draft
              </button>
            )}
            {canEdit && (
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
                <span className="meta-label">Last Updated</span>
                <span className="meta-value">{formatDate(request.updated_at)}</span>
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

        {/* Audit Timeline (admin only) */}
        {role === 'admin' && auditLogs.length > 0 && (
          <section className="card" style={{ marginTop: 16 }} aria-label="Audit timeline">
            <div className="card-header">
              <h3 className="card-title">Audit Timeline</h3>
            </div>
            <div className="card-body">
              <motion.ol
                className="audit-timeline"
                variants={STAGGER}
                initial="hidden"
                animate="show"
              >
                {auditLogs.map((log) => (
                  <motion.li key={log.id} className="audit-timeline__item" variants={ITEM}>
                    <span className="audit-timeline__dot" aria-hidden="true" />
                    <div className="audit-timeline__body">
                      <span className="audit-timeline__action">{actionLabel(log.action)}</span>
                      {log.note && (
                        <span className="audit-timeline__note">{log.note}</span>
                      )}
                      {(log.old_status || log.new_status) && (
                        <span className="audit-timeline__transition">
                          {log.old_status && <span className="audit-timeline__status">{log.old_status}</span>}
                          {log.old_status && log.new_status && <span>→</span>}
                          {log.new_status && <span className="audit-timeline__status">{log.new_status}</span>}
                        </span>
                      )}
                    </div>
                    <time className="audit-timeline__time" dateTime={log.created_at}>
                      {formatDateShort(log.created_at)}
                    </time>
                  </motion.li>
                ))}
              </motion.ol>
            </div>
          </section>
        )}
      </div>

      {/* Sidebar */}
      <aside className="detail-sidebar" aria-label="Request panels">
        {/* AI Review */}
        <AIReviewPanel requestId={request.id} />

        {/* Attachments */}
        <div className="card" style={{ marginTop: 16 }}>
          <div className="card-header">
            <h3 className="card-title">Attachments</h3>
          </div>
          <div className="card-body">
            {attachments.length === 0 ? (
              <p style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>No attachments.</p>
            ) : (
              <ul className="attachment-list">
                {attachments.map((att) => (
                  <li key={att.id} className="attachment-item attachment-item--done">
                    <span className="attachment-item__icon">📄</span>
                    <span className="attachment-item__name">{att.filename}</span>
                    <span className="attachment-item__size">{(att.file_size / 1024).toFixed(1)} KB</span>
                    <button
                      className="btn btn-ghost btn-sm"
                      style={{ padding: '2px 6px', fontSize: 11 }}
                      onClick={() => void handleDownload(att)}
                      aria-label={`Download ${att.filename}`}
                    >
                      ↓
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </aside>
    </div>
  )
}
