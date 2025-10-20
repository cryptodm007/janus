/**
 * Driver para a Base–Solana Bridge (placeholder Fase 0).
 * Na Fase 2, este pacote irá envolver os scripts/SDK do repositório vendor/bridge-base-solana.
 */
export interface SendMessageParams {
  payload: Uint8Array | string;
  direction: 'BASE_TO_SOLANA' | 'SOLANA_TO_BASE';
}
export interface MessageReceipt { txId?: string; status: 'QUEUED' }

export async function sendMessage(params: SendMessageParams): Promise<MessageReceipt> {
  // TODO(Fase 2): integrar com vendor/bridge-base-solana
  return { status: 'QUEUED' };
}
