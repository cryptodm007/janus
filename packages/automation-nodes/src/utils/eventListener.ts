import { ethers } from 'ethers';
import { Connection, PublicKey, SignaturesForAddressOptions } from '@solana/web3.js';

export async function listenEvmEvents(
  rpcWs: string | undefined,
  address: string,
  eventSignatureOrTopic: string,
  onEvent: (log: ethers.Log) => Promise<void> | void,
  onError: (err: Error) => void,
) {
  if (!rpcWs) throw new Error('Missing EVM WS RPC (JANUS_EVM_RPC_WS)');
  const provider = new ethers.WebSocketProvider(rpcWs);
  const topic = eventSignatureOrTopic.startsWith('0x')
    ? eventSignatureOrTopic
    : ethers.id(eventSignatureOrTopic);
  const filter = { address, topics: [topic] };

  const sub = provider.on(filter, async (log) => {
    try { await onEvent(log); } catch (e: any) { onError(e); }
  });

  provider._websocket.on('close', () => onError(new Error('EVM WS closed')));
  provider._websocket.on('error', (e: any) => onError(e));

  return () => {
    provider.off(filter, sub);
    provider.destroy();
  };
}

// Solana: polling simples de assinaturas recentes para um endereço (ex.: ProgramID ou ATA)
// Ideal trocar para WebSocket (onLogs) quando viável na sua infra.
export async function pollSolanaSignatures(
  rpcHttp: string,
  address: string,
  intervalMs: number,
  onSignature: (sig: string) => Promise<void> | void,
  onError: (err: Error) => void,
) {
  const conn = new Connection(rpcHttp, 'confirmed');
  const pubkey = new PublicKey(address);
  let before: string | undefined;

  const tick = async () => {
    try {
      const opts: SignaturesForAddressOptions = { before, limit: 20 };
      const list = await conn.getSignaturesForAddress(pubkey, opts);
      for (const item of list) {
        await onSignature(item.signature);
      }
      if (list.length > 0) before = list[list.length - 1].signature;
    } catch (e: any) { onError(e); }
  };

  const id = setInterval(tick, intervalMs);
  return () => clearInterval(id);
}
