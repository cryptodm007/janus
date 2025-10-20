import { runCommand, parseMaybeJson } from './cli';

export type Direction = 'BASE_TO_SOLANA' | 'SOLANA_TO_BASE';

export interface SendMessageParams {
  direction: Direction;
  payload: Uint8Array | string;
  intentId?: string;
  timeoutMs?: number;
}

export interface MessageReceipt {
  intentId?: string;
  txId?: string;
  status: 'QUEUED' | 'SENT' | 'PROVEN' | 'FINALIZED' | 'EXECUTED' | 'REJECTED';
  error?: string;
}

const BASE_CLI = process.env.BRIDGE_BASE_CLI || 'node vendor/bridge-base-solana/base/cli.js';
const SOLANA_CLI = process.env.BRIDGE_SOLANA_CLI || 'node vendor/bridge-base-solana/solana/cli.js';
const BASE_NET = process.env.BRIDGE_BASE_NETWORK || 'sepolia';
const SOLANA_NET = process.env.BRIDGE_SOLANA_NETWORK || 'devnet';
const WORKDIR = process.env.BRIDGE_WORKDIR || 'vendor/bridge-base-solana';

const MAX_WAIT_DEFAULT = Number(process.env.ADAPTER_MAX_WAIT_MS || 15 * 60_000);
const POLL_MS_DEFAULT = Number(process.env.ADAPTER_POLL_MS || 5_000);

function b64(input: Uint8Array | string): string {
  const buf = typeof input === 'string' ? Buffer.from(input, 'utf-8') : Buffer.from(input);
  return 'base64:' + buf.toString('base64');
}

export async function sendMessage(params: SendMessageParams): Promise<MessageReceipt> {
  const payloadB64 = b64(params.payload);
  const intentId = params.intentId || `intent-${Date.now()}`;

  if (params.direction === 'BASE_TO_SOLANA') {
    const r = await runCommand(BASE_CLI, ['init', '--network', BASE_NET, '--payload', payloadB64, '--intent', intentId], { cwd: WORKDIR });
    const js = parseMaybeJson(r.stdout) || {};
    if (!r.ok) {
      return { intentId, status: 'REJECTED', error: r.stderr || 'init failed' };
    }
    return { intentId: js.intentId || intentId, txId: js.txId, status: js.status || 'SENT' };
  } else {
    const r = await runCommand(SOLANA_CLI, ['init', '--network', SOLANA_NET, '--payload', payloadB64, '--intent', intentId], { cwd: WORKDIR });
    const js = parseMaybeJson(r.stdout) || {};
    if (!r.ok) {
      return { intentId, status: 'REJECTED', error: r.stderr || 'init failed' };
    }
    return { intentId: js.intentId || intentId, txId: js.txId, status: js.status || 'SENT' };
  }
}

export async function awaitProveAndFinalize(intentId: string, opts: { maxWaitMs?: number; pollMs?: number } = {}): Promise<MessageReceipt> {
  const maxWait = opts.maxWaitMs ?? MAX_WAIT_DEFAULT;
  const poll = opts.pollMs ?? POLL_MS_DEFAULT;
  const start = Date.now();

  while (Date.now() - start < maxWait) {
    const p = await runCommand(SOLANA_CLI, ['prove', '--network', SOLANA_NET, '--intent', intentId], { cwd: WORKDIR });
    if (!p.ok) {
      await new Promise(r => setTimeout(r, poll));
      continue;
    }
    const f = await runCommand(SOLANA_CLI, ['finalize', '--network', SOLANA_NET, '--intent', intentId], { cwd: WORKDIR });
    const js = parseMaybeJson(f.stdout) || {};
    if (f.ok) {
      return { intentId, txId: js.txId, status: js.status || 'FINALIZED' };
    }
    await new Promise(r => setTimeout(r, poll));
  }
  return { intentId, status: 'REJECTED', error: 'timeout' };
}

export async function getStatus(intentId: string): Promise<MessageReceipt> {
  const b = await runCommand(BASE_CLI, ['status', '--network', BASE_NET, '--intent', intentId], { cwd: WORKDIR });
  const bj = parseMaybeJson(b.stdout) || {};
  if (b.ok && (bj.status || bj.txId)) return { intentId, txId: bj.txId, status: bj.status || 'SENT' };

  const s = await runCommand(SOLANA_CLI, ['status', '--network', SOLANA_NET, '--intent', intentId], { cwd: WORKDIR });
  const sj = parseMaybeJson(s.stdout) || {};
  if (s.ok && (sj.status || sj.txId)) return { intentId, txId: sj.txId, status: sj.status || 'SENT' };

  return { intentId, status: 'QUEUED' };
}
