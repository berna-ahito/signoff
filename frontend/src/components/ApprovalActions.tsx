import { useState } from 'react'
import { decide } from '../api/approvals'
import type { Decision, RequestDetail, Role } from '../types'

interface Props {
  request: RequestDetail
  role: Role | null
  onDecision: () => void
}

const decisionConfig: Record<Decision, { label: string; typeClass: string; btnClass: string }> = {
  approved: { label: 'Approve', typeClass: 'decision-approve', btnClass: 'btn-success' },
  rejected: { label: 'Reject', typeClass: 'decision-reject', btnClass: 'btn-danger' },
  needs_more_info: { label: 'Need More Info', typeClass: 'decision-info', btnClass: 'btn-outline' },
}

export function ApprovalActions({ request, role, onDecision }: Props) {
  const [decision, setDecision] = useState<Decision | null>(null)
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canDecide =
    request.status === 'pending_approval' &&
    (role === 'admin' || role === request.assigned_role)

  if (!canDecide) return null

  async function submit() {
    if (!decision) return
    setLoading(true)
    setError(null)
    try {
      await decide(request.id, { decision, note: note || undefined })
      onDecision()
    } catch (e: unknown) {
      const axiosErr = e as { response?: { data?: { detail?: string } }; message?: string }
      const msg = axiosErr?.response?.data?.detail ?? axiosErr?.message ?? 'Failed to submit decision'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const activeConfig = decision ? decisionConfig[decision] : null

  return (
    <>
    <div className="section-label">Decision Required</div>
    <section className="card card-prominent" aria-labelledby="approval-actions-heading">
      <div className="card-header">
        <h2 className="card-title" id="approval-actions-heading">Your Decision</h2>
      </div>
      <div className="card-body stack">
        {error && <div className="alert alert-error" role="alert">{error}</div>}

        <fieldset style={{ border: 'none' }}>
          <legend className="form-label" style={{ marginBottom: 8 }}>Select decision</legend>
          <div className="decision-options" role="group" aria-label="Decision options">
            {(Object.entries(decisionConfig) as [Decision, typeof decisionConfig[Decision]][]).map(([d, cfg]) => (
              <label
                key={d}
                className={`decision-option ${cfg.typeClass} ${decision === d ? 'selected' : ''}`}
              >
                <input
                  type="radio"
                  name="decision"
                  value={d}
                  checked={decision === d}
                  onChange={() => setDecision(d)}
                  className="sr-only"
                />
                {cfg.label}
              </label>
            ))}
          </div>
        </fieldset>

        <div className="form-group">
          <label htmlFor="approval-note" className="form-label">
            Note <span className="text-muted">(optional)</span>
          </label>
          <textarea
            id="approval-note"
            className="form-textarea"
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Add a note for this decision…"
          />
        </div>

        <div className="row">
          <button
            className={`btn ${activeConfig?.btnClass ?? 'btn-outline'}`}
            onClick={submit}
            disabled={!decision || loading}
            aria-busy={loading}
          >
            {loading ? <><span className="spinner" aria-hidden="true" /> Submitting…</> : 'Submit Decision'}
          </button>
        </div>

        <p className="human-control-note">
          Your decision is final and will be recorded in the audit trail. AI analysis above is advisory only.
        </p>
      </div>
    </section>
    </>
  )
}
