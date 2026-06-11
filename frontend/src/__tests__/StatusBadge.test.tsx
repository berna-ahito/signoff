import { render, screen } from '@testing-library/react'
import { StatusBadge } from '../components/StatusBadge'
import type { RequestStatus } from '../types'

describe('StatusBadge', () => {
  it('renders approved status with correct label', () => {
    render(<StatusBadge status="approved" />)
    expect(screen.getByText('Approved')).toBeInTheDocument()
  })

  it('renders all 7 status values without crashing', () => {
    const statuses: RequestStatus[] = [
      'draft',
      'pending_review',
      'pending_approval',
      'needs_rule',
      'approved',
      'rejected',
      'needs_more_info',
    ]
    for (const status of statuses) {
      const { unmount } = render(<StatusBadge status={status} />)
      unmount()
    }
  })

  it.each([
    ['draft', 'Draft', 'badge-draft'],
    ['pending_review', 'In Review', 'badge-pending'],
    ['pending_approval', 'Pending Approval', 'badge-approval'],
    ['needs_rule', 'Needs Routing', 'badge-rule'],
    ['approved', 'Approved', 'badge-approved'],
    ['rejected', 'Rejected', 'badge-rejected'],
    ['needs_more_info', 'Needs Info', 'badge-info'],
  ] as [RequestStatus, string, string][])(
    'renders %s with CSS class %s',
    (status, label, cls) => {
      render(<StatusBadge status={status} />)
      const badge = screen.getByLabelText(`Status: ${label}`)
      expect(badge).toHaveClass(cls)
    },
  )

  it('uses badge-unknown class and raw text for unrecognised status', () => {
    render(<StatusBadge status={'galaxy_brain' as RequestStatus} />)
    const badge = screen.getByLabelText('Status: galaxy_brain')
    expect(badge).toHaveClass('badge-unknown')
    expect(badge).toHaveTextContent('galaxy_brain')
  })
})
