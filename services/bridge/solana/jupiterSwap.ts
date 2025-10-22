import axios from "axios";
import { Connection, Keypair, VersionedTransaction, PublicKey } from "@solana/web3.js";

type JupParams = {
  inputMint: string;     // ex: USDC mint
  outputMint: string;    // ex: SOL (WSOL) mint
  amount: string;        // em unidades inteiras do inputToken (lamports, etc.)
  slippageBps?: number;  // default 50 bps
};

export async function jupiterSwap(params: JupParams) {
  const conn = new Connection(process.env.SOLANA_RPC_URL!, "confirmed");
  const payer = Keypair.fromSecretKey(Uint8Array.from(JSON.parse(process.env.SOLANA_PAYER_SECRET_KEY_JSON!)));
  const owner = payer.publicKey.toBase58();
  const jupQ  = process.env.JUP_API_URL || "https://quote-api.jup.ag/v6/quote";
  const jupS  = process.env.JUP_SWAP_URL || "https://quote-api.jup.ag/v6/swap";
  const bps   = params.slippageBps ?? 50;

  // 1) Quote
  const { data: quote } = await axios.get(jupQ, {
    params: {
      inputMint: params.inputMint,
      outputMint: params.outputMint,
      amount: params.amount,
      slippageBps: bps,
      onlyDirectRoutes: false
    }, timeout: 12000
  });

  if (!quote || !quote.routePlan?.length) throw new Error("Jupiter: nenhuma rota");

  // 2) Obter transação de swap serializada
  const { data: swapTxResp } = await axios.post(jupS, {
    quoteResponse: quote,
    userPublicKey: owner,
    wrapAndUnwrapSol: true
  }, { timeout: 12000 });

  const swapTx = swapTxResp.swapTransaction;
  const tx = VersionedTransaction.deserialize(Buffer.from(swapTx, "base64"));
  tx.sign([payer]);

  const txSig = await conn.sendTransaction(tx);
  const conf = await conn.confirmTransaction(txSig, "confirmed");

  return { chain: "solana", txHash: txSig, slot: conf.context.slot };
}
