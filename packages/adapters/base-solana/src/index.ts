/**
 * Adapter Base–Solana (Fase 2)
 * - Nesta fase, métodos são stubs para habilitar o desenvolvimento do Gateway.
 * - Na próxima etapa, conectaremos com vendor/bridge-base-solana (submódulo).
 */

export type Direction = 'BASE_TO_SOLANA' | 'SOLANA_TO_BASE';

export interface SendMessageParams {
  direction: Direction;
  payload: Uint8Array | string;  // envelope serializado
  // metadados opcionais
  intentId?: string;
  timeoutMs?: number;
}

export interface MessageReceipt {
  intentId?: string;
  txId?: string;
  status: 'QUEUED' | 'SENT' | 'PROVEN' | 'FINALIZED' | 'EXECUTED' | 'REJECTED';
  error?: string;
}

export async function sendMessage(params: SendMessageParams): Promise<MessageReceipt> {
  // TODO(Fase 2b): chamar scripts/SDK da vendor/bridge-base-solana
  // Retornamos QUEUED para permitir que o Gateway trate orquestração/polling.
  return {
    intentId: params.intentId,
    status: 'QUEUED'
  };
}

/**
 * Aguarda etapas específicas para Base→Solana (prove/finalize), com polling/backoff.
 * Aqui fica um stub com retry simples.
 */
export async function awaitProveAndFinalize(
  intentId: string,
  opts: { maxWaitMs?: number; pollMs?: number } = {}
): Promise<MessageReceipt> {
  const maxWait = opts.maxWaitMs ?? 15 * 60_000;  // ~15 minutos padrao
  const poll = opts.pollMs ?? 5_000;              // 5s entre polls
  const start = Date.now();

  // STUB: apenas espera o tempo mínimo e devolve FINALIZED
  while (Date.now() - start < maxWait) {
    await new Promise(r => setTimeout(r, poll));
    // critério mock: marcamos como FINALIZED após um ciclo
    return { intentId, status: 'FINALIZED' };
  }
  return { intentId, status: 'REJECTED', error: 'timeout' };
}

export async function getStatus(intentId: string): Promise<MessageReceipt> {
  // STUB: retorna status FIXO
  return { intentId, status: 'QUEUED' };
}
