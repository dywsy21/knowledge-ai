const API_BASE = import.meta.env.VITE_API_BASE || '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed: ${response.status}`)
  }

  return response.json()
}

export const api = {
  summary: () => request('/summary'),
  sources: () => request('/sources'),
  interactions: () => request('/interactions'),
  fullChain: (payload) =>
    request('/full-chain', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  extractSource: (sourceId) => request(`/sources/${sourceId}/extract`, { method: 'POST' }),
  createInteraction: (payload) =>
    request('/interactions', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  submitFeedback: (payload) =>
    request('/feedback', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
}
