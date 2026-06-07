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
})
