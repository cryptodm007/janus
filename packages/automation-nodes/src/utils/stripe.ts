const STRIPE_SECRET = process.env.STRIPE_SECRET_KEY || '';
const API = process.env.STRIPE_API_BASE || 'https://api.stripe.com/v1';

function formEncode(obj: Record<string, any>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(obj)) {
    if (v === undefined || v === null) continue;
    if (typeof v === 'object') {
      // Apenas o básico: para arrays simples tipo line_items[0][price]=... use já montado no "extra"
      p.set(k, JSON.stringify(v));
    } else {
      p.set(k, String(v));
    }
  }
  return p.toString();
}

export async function stripePost(path: string, body: Record<string, any>) {
  if (!STRIPE_SECRET) throw new Error('Missing STRIPE_SECRET_KEY');
  const res = await fetch(`${API}/${path.replace(/^\//, '')}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${STRIPE_SECRET}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formEncode(body),
  } as any);
  if (!res.ok) throw new Error(`Stripe POST ${path} failed: ${res.status} ${res.statusText} - ${await res.text()}`);
  return res.json();
}
