import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { LoginPage } from '../pages/LoginPage'

vi.mock('axios')

describe('LoginPage', () => {
  it('renders email and password fields', () => {
    render(
      <MemoryRouter>
        <LoginPage onLogin={vi.fn()} />
      </MemoryRouter>
    )
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
  })

  it('calls onLogin with email and password on form submit', async () => {
    const mockLogin = vi.fn().mockResolvedValue('requester')
    render(
      <MemoryRouter>
        <LoginPage onLogin={mockLogin} />
      </MemoryRouter>
    )

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'alice@test.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'alice123' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('alice@test.com', 'alice123')
    })
  })

  it('shows error message when login fails', async () => {
    const mockLogin = vi.fn().mockRejectedValue(new Error('Invalid credentials'))
    render(
      <MemoryRouter>
        <LoginPage onLogin={mockLogin} />
      </MemoryRouter>
    )

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'bad@test.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
    expect(screen.getByText('Invalid email or password.')).toBeInTheDocument()
  })
})
