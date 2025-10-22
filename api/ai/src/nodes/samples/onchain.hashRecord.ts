import crypto from "crypto";

/**
 * Demonstra cálculo de hash de um registro e o "commit" fictício on-chain.
 * Substituir por chamada real ao core que registra em Base/Solana.
 */
export async function onchainHashRecord(params: any) {
  const { data } = params;
  if (!data) throw new Error("data required");
  const hash = crypto.createHash("sha256").update(JSON.stringify(data)).digest("hex");
  // TODO: submit tx ao contrato (commit do hash)
  return { hash, txId: `0xhash_${Date.now()}` };
}
