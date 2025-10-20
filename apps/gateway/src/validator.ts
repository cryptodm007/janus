import { MCPJanusEnvelope } from './types';

export function validateEnvelope(body: any): { ok: true; data: MCPJanusEnvelope } | { ok: false; error: string } {
  if (!body || typeof body !== 'object') return { ok: false, error: 'body must be an object' };
  if (body.type !== 'request') return { ok: false, error: 'type must be request' };
  if (!body.id || typeof body.id !== 'string') return { ok: false, error: 'id is required' };
  if (!body.method || typeof body.method !== 'string') return { ok: false, error: 'method is required' };
  if (typeof body.params !== 'object') return { ok: false, error: 'params must be object' };
  if (!body.chain || typeof body.chain !== 'object') return { ok: false, error: 'chain is required' };
  const { origin, destination, executor, signature } = body.chain;
  if (!origin || !destination || !executor || !signature) return { ok: false, error: 'chain fields missing' };
  return { ok: true, data: body as MCPJanusEnvelope };
}
