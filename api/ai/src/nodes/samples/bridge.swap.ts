import { evmSwapBase } from "../../../../services/bridge/base/evmSwap.js";
import { jupiterSwap } from "../../../../services/bridge/solana/jupiterSwap.js";

/**
 * Node de swap multichain simples (não-bridge): executa no DEX nativo de cada chain.
 * Params esperados:
 *  - chain: "base" | "solana"
 *  - tokenIn / tokenOut (EVM: símbolo ou endereço; Solana: mints)
 *  - amount: string (em unidades mínimas: wei/lamports)
 *  - slippageBps?: number
 */
export async function bridgeSwap(params: any) {
  const { chain, tokenIn, tokenOut, amount, slippageBps } = params || {};
  if (!chain || !tokenIn || !tokenOut || !amount) throw new Error("chain/tokenIn/tokenOut/amount required");

  if (chain === "base") {
    // EVM via 0x (Base)
    return evmSwapBase({
      sellToken: tokenIn,
      buyToken: tokenOut,
      amount,
      slippageBps
    });
  }

  if (chain === "solana") {
    // Solana via Jupiter
    return jupiterSwap({
      inputMint: tokenIn,
      outputMint: tokenOut,
      amount,
      slippageBps
    });
  }

  throw new Error(`chain não suportada: ${chain}`);
}
