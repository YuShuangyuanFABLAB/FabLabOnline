import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('API Client', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('registers a 401 response interceptor', async () => {
    const mockResponseUse = vi.fn()
    vi.doMock('axios', () => ({
      default: {
        create: () => ({
          interceptors: {
            response: { use: mockResponseUse },
          },
          get: vi.fn(),
          post: vi.fn(),
          put: vi.fn(),
          delete: vi.fn(),
        }),
      },
    }))

    await import('@/api/client')
    expect(mockResponseUse).toHaveBeenCalledTimes(1)
    expect(mockResponseUse).toHaveBeenCalledWith(expect.any(Function), expect.any(Function))
  })

  it('does not use localStorage for token storage', async () => {
    // Verify client.ts has no localStorage references
    const fs = await import('fs')
    const path = await import('path')
    const clientCode = fs.readFileSync(
      path.resolve(import.meta.dirname, '../api/client.ts'),
      'utf-8',
    )
    expect(clientCode).not.toContain('localStorage')
  })
})
