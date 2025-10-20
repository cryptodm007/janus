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
  };
}
