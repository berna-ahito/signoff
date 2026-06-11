import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RequestFormPage } from '../pages/RequestFormPage'
import type { Attachment, RequestDetail } from '../types'

const {
  mockUseParams,
  mockNavigate,
  mockCreateRequest,
  mockGetRequest,
  mockListAttachments,
} = vi.hoisted(() => ({
  mockUseParams: vi.fn(),
  mockNavigate: vi.fn(),
  mockCreateRequest: vi.fn(),
  mockGetRequest: vi.fn(),
  mockListAttachments: vi.fn(),
}))

vi.mock('react-router-dom', () => ({
  useParams: mockUseParams,
  useNavigate: () => mockNavigate,
}))

vi.mock('../api/requests', () => ({
  createRequest: mockCreateRequest,
  getRequest: mockGetRequest,
  updateRequest: vi.fn(),
  submitRequest: vi.fn(),
}))

vi.mock('../api/attachments', () => ({
  listAttachments: mockListAttachments,
  uploadAttachment: vi.fn(),
}))

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

const BASE_REQUEST: RequestDetail = {
  id: 1,
  title: 'Existing',
  description: 'Desc',
  category: 'IT',
  urgency: 'medium',
  quantity: 1,
  estimated_cost: 100,
  vendor_id: null,
  justification: 'Just',
  status: 'draft',
  requester_id: 1,
  assigned_role: null,
  created_at: '2024-01-01T00:00:00',
  updated_at: '2024-01-01T00:00:00',
}

function makeAttachment(id: number): Attachment {
  return {
    id,
    request_id: 1,
    filename: `att${id}.pdf`,
    content_type: 'application/pdf',
    file_size: 1024,
    uploader_id: 1,
    created_at: '2024-01-01T00:00:00',
  }
}

describe('RequestFormPage', () => {
  beforeEach(() => {
    mockUseParams.mockReturnValue({})
    mockGetRequest.mockResolvedValue(BASE_REQUEST)
    mockListAttachments.mockResolvedValue([])
    mockCreateRequest.mockResolvedValue({ id: 99 })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows "Title is required." when submitting new request with empty title', async () => {
    render(<RequestFormPage />)

    await userEvent.click(screen.getByRole('button', { name: 'Submit for Review' }))

    expect(screen.getByText('Title is required.')).toBeInTheDocument()
  })

  it('shows "Exceeds 5 MB limit." for an oversized file in edit mode', async () => {
    mockUseParams.mockReturnValue({ id: '1' })
    const { container } = render(<RequestFormPage />)

    const fileInput = await waitFor(() => {
      const el = container.querySelector('input[type="file"]')
      if (!el) throw new Error('file input not mounted yet')
      return el as HTMLInputElement
    })

    const bigFile = new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'big.pdf', {
      type: 'application/pdf',
    })
    Object.defineProperty(fileInput, 'files', { value: [bigFile], configurable: true })
    fireEvent.change(fileInput)

    expect(await screen.findByText('Exceeds 5 MB limit.')).toBeInTheDocument()
  })

  it('shows "Maximum 5 files allowed." when adding a file with 5 attachments already present', async () => {
    mockUseParams.mockReturnValue({ id: '1' })
    mockListAttachments.mockResolvedValue(
      Array.from({ length: 5 }, (_, i) => makeAttachment(i + 1)),
    )
    const { container } = render(<RequestFormPage />)

    const fileInput = await waitFor(() => {
      const el = container.querySelector('input[type="file"]')
      if (!el) throw new Error('file input not mounted yet')
      return el as HTMLInputElement
    })

    const newFile = new File(['content'], 'new.pdf', { type: 'application/pdf' })
    Object.defineProperty(fileInput, 'files', { value: [newFile], configurable: true })
    fireEvent.change(fileInput)

    expect(await screen.findByText('Maximum 5 files allowed.')).toBeInTheDocument()
  })

  it('does not show "Title is required." when all required fields are filled before submit', async () => {
    render(<RequestFormPage />)

    await userEvent.type(
      screen.getByPlaceholderText(/ergonomic chairs/i),
      'New laptop',
    )
    await userEvent.type(
      screen.getByPlaceholderText(/describe what you need/i),
      'For dev work',
    )
    await userEvent.type(
      screen.getByPlaceholderText(/business justification/i),
      'Required',
    )
    const costInput = screen.getByPlaceholderText('0.00')
    await userEvent.clear(costInput)
    await userEvent.type(costInput, '500')

    await userEvent.click(screen.getByRole('button', { name: 'Submit for Review' }))

    expect(screen.queryByText('Title is required.')).not.toBeInTheDocument()
  })

  it('calls createRequest and does not show "Description is required." when saving draft with title only', async () => {
    render(<RequestFormPage />)

    await userEvent.type(
      screen.getByPlaceholderText(/ergonomic chairs/i),
      'Only a title',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Save as Draft' }))

    await waitFor(() => expect(mockCreateRequest).toHaveBeenCalledOnce())
    expect(screen.queryByText('Description is required.')).not.toBeInTheDocument()
  })
})
