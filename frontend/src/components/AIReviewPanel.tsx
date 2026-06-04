import { useState } from 'react'
import { getAIReview } from '../api/requests'
import type { AIReview } from '../types'
import './AIReviewPanel.css'

interface Props {
  requestId: number
}

const actionLabels: Record<AIReview['recommended_action'], string> = {
  request_more_info: 'Request More Info',
  manager_review: 'Manager Review',
  finance_review: 'Finance Review',
  ready_for_rfq: 'Ready for RFQ',
}

const riskClass: Record<string, string> = {
  low: 'risk-low',
  medium: 'risk-medium',
  high: 'risk-high',
}

export function AIReviewPanel({ requestId }: Props) {
  const [review, setReview] = useState<AIReview | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function runReview() {
    setLoading(true)
    setError(null)
    try {
      const result = await getAIReview(requestId)
      setReview(result)
    } catch {
      setError('Failed to generate AI review. Ensure the request is in a reviewable state.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="ai-panel card" aria-labelledby="ai-panel-heading">
      <div className="card-header">
        <h2 className="card-title" id="ai-panel-heading">
          <span className="ai-badge" aria-hidden="true">AI</span>
          Automated Analysis
          <span className="ai-advisory-chip" aria-hidden="true">advisory</span>
        </h2>
        {!review && (
          <button
            className="btn btn-outline btn-sm"
            onClick={runReview}
            disabled={loading}
            aria-busy={loading}
          >
            {loading ? <><span className="spinner" role="status" aria-label="Loading" /> Running…</> : 'Run Analysis'}
          </button>
        )}
      </div>

      <div className="card-body" style={{ paddingBottom: 10 }}>
        <p className="ai-disclaimer" role="note">
          AI analysis is <strong>advisory only</strong>. All approval decisions are made by authorized humans and logged to the audit trail.
        </p>
      </div>

      {error && (
        <div className="card-body" style={{ paddingTop: 0 }}>
          <div className="alert alert-error" role="alert">{error}</div>
        </div>
      )}

      {!review && !error && !loading && (
        <div className="card-body empty-state" style={{ padding: '16px', paddingTop: 0 }}>
          <p className="text-muted text-sm">Click "Run Analysis" to generate an AI assessment of this request.</p>
        </div>
      )}

      {review && (
        <div className="card-body stack" style={{ gap: 14, paddingTop: 0 }}>
          <div className="ai-summary">{review.summary}</div>

          <div className="ai-metrics">
            <div className="ai-metric">
              <span className="meta-label">Risk</span>
              <span className={`ai-pill ${riskClass[review.risk_level]}`}>{review.risk_level}</span>
            </div>
            <div className="ai-metric">
              <span className="meta-label">Urgency</span>
              <span className={`ai-pill ${riskClass[review.urgency]}`}>{review.urgency}</span>
            </div>
            <div className="ai-metric">
              <span className="meta-label">Confidence</span>
              <span className="ai-confidence">
                <span className="ai-confidence-bar-track">
                  <span
                    className="ai-confidence-bar"
                    style={{ width: `${review.confidence * 100}%` }}
                    role="meter"
                    aria-valuenow={Math.round(review.confidence * 100)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`Confidence: ${Math.round(review.confidence * 100)}%`}
                  />
                </span>
                <span className="ai-confidence-label">{Math.round(review.confidence * 100)}%</span>
              </span>
            </div>
            <div className="ai-metric">
              <span className="meta-label">Suggestion</span>
              <span className="meta-value">{actionLabels[review.recommended_action]}</span>
            </div>
          </div>

          {review.missing_info.length > 0 && (
            <div>
              <p className="ai-rfq-section-label" style={{ marginBottom: 6 }}>Missing Information</p>
              <ul className="ai-missing-list" aria-label="Missing information items">
                {review.missing_info.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <p className="ai-rfq-section-label">RFQ Draft</p>
            <pre className="ai-rfq-draft">{review.rfq_draft}</pre>
          </div>
        </div>
      )}
    </section>
  )
}
