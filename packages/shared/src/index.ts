export type Chain = 'Base' | 'Solana';
export interface ChainEnvelope {
  origin: Chain; destination: Chain; executor: string; signature: string; constitution?: string;
}
