import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AIReviewPanel } from '../components/AIReviewPanel'
import * as requestsApi from '../api/requests'
import type { AIReview } from '../types'

vi.mock('../api/requests')

const mockReview: AIReview = {
  summary: 'Low-risk IT equipment purchase within budget.',
  category: 'IT',
  urgency: 'low',
  risk_level: 'low',
  missing_info: [],
  recommended_action: 'manager_review',
  rfq_draft: 'Request for Quotation: 1x laptop',
  confidence: 0.87,
}

describe('AIReviewPanel', () => {
  it('renders Run Analysis button initially without review data', () => {
    render(<AIReviewPanel requestId={1} />)
    expect(screen.getByText('Run Analysis')).toBeInTheDocument()
  })

  it('renders AI review data after triggering analysis', async () => {
    vi.mocked(requestsApi.getAIReview).mockResolvedValue(mockReview)

    render(<AIReviewPanel requestId={1} />)
    fireEvent.click(screen.getByText('Run Analysis'))

    await waitFor(() => {
      expect(screen.getByText(mockReview.summary)).toBeInTheDocument()
    })
    expect(screen.getAllByText('low').length).toBeGreaterThan(0)
  })
})
