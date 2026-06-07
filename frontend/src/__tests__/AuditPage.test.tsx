import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuditPage } from '../pages/AuditPage'
import * as auditApi from '../api/audit'

vi.mock('../api/audit')

describe('AuditPage', () => {
  it('renders loading state initially', () => {
    vi.mocked(auditApi.listAuditLogs).mockReturnValue(new Promise(() => {}))
    render(
      <MemoryRouter>
        <AuditPage />
      </MemoryRouter>
    )
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders audit log table rows after data loads', async () => {
    vi.mocked(auditApi.listAuditLogs).mockResolvedValue([
      {
        id: 1,
        request_id: 10,
        actor_id: 2,
        action: 'submitted',
        old_status: 'draft',
        new_status: 'pending_review',
        note: null,
        created_at: '2026-01-01T00:00:00Z',
      },
    ])

    render(
      <MemoryRouter>
        <AuditPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('submitted')).toBeInTheDocument()
    })
  })
})
