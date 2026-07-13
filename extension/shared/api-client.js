// Shared API client for extension to call backend
export async function apiFetch(endpoint, options = {}) {
  const baseUrl = options.baseUrl || 'http://localhost:8000';
  const response = await fetch(`${baseUrl}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  });
  if (!response.ok) {
    const err = await response.text();
    throw new Error(`API error ${response.status}: ${err}`);
  }
  return response.json();
}
