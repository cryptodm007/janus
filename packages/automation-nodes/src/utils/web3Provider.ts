// Helper HTTP client genérico para provedores Web3 externos via API.
// Configure via ENV (sem citar marcas): JANUS_PROVIDER_BASE_URL, JANUS_PROVIDER_API_KEY.
const BASE_URL = process.env.JANUS_PROVIDER_BASE_URL || 'https://api.web3-provider.example';
const API_KEY = process.env.JANUS_PROVIDER_API_KEY;

export type ProviderMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

export async function providerRequest<T = any>(
  path: string,
  method: ProviderMethod = 'GET',
  body?: any,
  headers?: Record<string, string>,
): Promise<T> {
  if (!API_KEY) throw new Error('Missing JANUS_PROVIDER_API_KEY env var');
  const url = `${BASE_URL.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;

  const res = await fetch(url, {
    method,
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
      ...(headers || {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  } as any);

  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`Provider ${method} ${url} failed: ${res.status} ${res.statusText} - ${txt}`);
  }

  try { return await res.json(); } catch { return (await res.text()) as any; }
}

export function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
