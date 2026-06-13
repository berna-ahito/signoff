import { createRef } from 'react'
import { render } from '@testing-library/react'
import { Button } from '../components/ui/button'

describe('Button', () => {
  it('forwards refs to the underlying button element', () => {
    const ref = createRef<HTMLButtonElement>()

    render(<Button ref={ref}>Save</Button>)

    expect(ref.current).toBeInstanceOf(HTMLButtonElement)
  })
})
