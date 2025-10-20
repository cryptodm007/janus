import Ajv from 'ajv';
import fetch from 'node-fetch';
import schema from '@janus/mcp-spec/schemas/mcp-janus-envelope.schema.json' assert { type: 'json' };

export type Chain = 'Base' | 'Solana';

export interface MCPJanusEnvelope {
  type: 'request';
  id: string;
  method: string;
  params: Record<string, unknown>;
  chain: {
    origin: Chain;
    destination: Chain;
    executor: string;
    signature: string;
    constitution?: string;
    nonce?: string;
    deadline: number;
  };
}

export type Status = 'QUEUED'|'SENT'|'PROVEN'|'FINALIZED'|'EXECUTED'|'REJECTED';

export interface SendIntentResponse {
  ok: boolean;
  id?: string;
  status?: Status;
  error?: string;
}

export interface SDKOptions {
  baseURL: string;           // ex.: http://localhost:8080
  apiKey?: string;           // se você adicionar auth depois
  timeoutMs?: number;        // timeout do fetch
}

const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema as any);

export class JanusClient {
  private baseURL: string;
  private apiKey?: string;
  private timeoutMs: number;

  constructor(opts: SDKOptions) {
    this.baseURL = opts.baseURL.replace(/\/+$/, '');
    this.apiKey = opts.apiKey;
    this.timeoutMs = opts.timeoutMs ?? 60_000;
  }

  validateEnvelope(envelope: MCPJanusEnvelope): { ok: true } | { ok: false; errors: string[] } {
    const ok = validate(envelope);
    if (ok) return { ok: true };
    const errors = (validate.errors || []).map(e => `${e.instancePath} ${e.message}`);
    return { ok: false, errors };
  }

  async sendIntent(envelope: MCPJanusEnvelope): Promise<SendIntentResponse> {
    const v = this.validateEnvelope(envelope);
    if (!v.ok) {
      return { ok: false, error: `invalid envelope: ${v.errors.join('; ')}` };
    }

    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), this.timeoutMs);

    try {
      const res = await fetch(`${this.baseURL}/mcp/intent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {})
        },
        body: JSON.stringify(envelope),
        signal: ctrl.signal
      });
      clearTimeout(t);
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        return { ok: false, error: body?.error || `http_${res.status}` };
      }
      return { ok: true, id: body.id, status: body.status };
    } catch (e: any) {
      clearTimeout(t);
      return { ok: false, error: String(e?.message || e) };
    }
  }

  async awaitResult(intentId: string, opts: { maxWaitMs?: number; pollMs?: number } = {}): Promise<SendIntentResponse> {
    const maxWait = opts.maxWaitMs ?? 15 * 60_000; // 15 min
    const pollMs = opts.pollMs ?? 5_000;
    const start = Date.now();

    while (Date.now() - start < maxWait) {
      const s = await this.getStatus(intentId);
      if (s.ok && s.status && (s.status === 'FINALIZED' || s.status === 'EXECUTED' || s.status === 'REJECTED')) {
        return s;
      }
      await new Promise(r => setTimeout(r, pollMs));
    }
    return { ok: false, id: intentId, status: 'REJECTED', error: 'timeout' };
  }

  async getStatus(intentId: string): Promise<SendIntentResponse> {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), this.timeoutMs);

    try {
      const res = await fetch(`${this.baseURL}/mcp/status/${encodeURIComponent(intentId)}`, {
        method: 'GET',
        headers: {
          ...(this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {})
        },
        signal: ctrl.signal
      });
      clearTimeout(t);
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        return { ok: false, error: body?.error || `http_${res.status}` };
      }
      return { ok: true, id: body.id || intentId, status: body.status };
    } catch (e: any) {
      clearTimeout(t);
      return { ok: false, error: String(e?.message || e) };
    }
  }
}
