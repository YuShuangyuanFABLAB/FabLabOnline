import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('API Client', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('registers a 401 response interceptor', async () => {
    const mockUse = vi.fn()
    vi.doMock('axios', () => ({
      default: {
        create: () => ({
          interceptors: {
            response: { use: mockUse },
          },
          get: vi.fn(),
          post: vi.fn(),
          put: vi.fn(),
          delete: vi.fn(),
        }),
      },
    }))

    await import('@/api/client')
    expect(mockUse).toHaveBeenCalledTimes(1)
    // First arg = success handler, second arg = error handler
    expect(mockUse).toHaveBeenCalledWith(expect.any(Function), expect.any(Function))
  })
})
