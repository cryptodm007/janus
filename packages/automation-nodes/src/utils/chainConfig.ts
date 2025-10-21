export type EvmNetwork = 'base-sepolia' | 'base-mainnet' | 'evm-custom';
export type SolanaNetwork = 'solana-devnet' | 'solana-mainnet' | 'solana-custom';

export const EVM_DEFAULTS: Record<EvmNetwork, { chainId: number; rpcHttp?: string; rpcWs?: string }> = {
  'base-sepolia': { chainId: 84532, rpcHttp: process.env.JANUS_EVM_RPC_HTTP, rpcWs: process.env.JANUS_EVM_RPC_WS },
  'base-mainnet': { chainId: 8453, rpcHttp: process.env.JANUS_EVM_RPC_HTTP, rpcWs: process.env.JANUS_EVM_RPC_WS },
  'evm-custom':  { chainId: Number(process.env.JANUS_EVM_CHAIN_ID || 0), rpcHttp: process.env.JANUS_EVM_RPC_HTTP, rpcWs: process.env.JANUS_EVM_RPC_WS },
};

export const SOLANA_DEFAULTS: Record<SolanaNetwork, { rpcHttp?: string }> = {
  'solana-devnet': { rpcHttp: process.env.JANUS_SOLANA_RPC_HTTP || 'https://api.devnet.solana.com' },
  'solana-mainnet': { rpcHttp: process.env.JANUS_SOLANA_RPC_HTTP || 'https://api.mainnet-beta.solana.com' },
  'solana-custom': { rpcHttp: process.env.JANUS_SOLANA_RPC_HTTP },
};
