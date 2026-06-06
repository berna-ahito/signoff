import { render, screen } from '@testing-library/react'
import { ApprovalActions } from '../components/ApprovalActions'
import type { RequestDetail } from '../types'

vi.mock('../api/approvals')

const baseRequest: RequestDetail = {
  id: 1,
  title: 'Test Request',
  description: 'Desc',
  category: 'IT',
  urgency: 'medium',
  quantity: 1,
  estimated_cost: 500,
  vendor_id: null,
  justification: 'Needed',
  status: 'pending_approval',
  requester_id: 1,
  assigned_role: 'manager',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('ApprovalActions', () => {
  it('renders null when user role cannot decide', () => {
    const { container } = render(
      <ApprovalActions
        request={{ ...baseRequest, status: 'pending_review' }}
        role="requester"
        onDecision={vi.fn()}
      />
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('renders decision buttons when user role can decide', () => {
    render(
      <ApprovalActions
        request={baseRequest}
        role="manager"
        onDecision={vi.fn()}
      />
    )
    expect(screen.getByText('Submit Decision')).toBeInTheDocument()
  })
})
