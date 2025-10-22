import axios from "axios";
import { ethers } from "ethers";

type SwapParams = {
  sellToken: string;   // ex: 'USDC' ou endereço 0x...
  buyToken: string;    // ex: 'WETH' ou endereço 0x...
  amount: string;      // em unidades do sellToken (wei se endereço)
  taker?: string;      // opcional: usará wallet do signer se omitido
  slippageBps?: number;
};

function toQuery(p: Record<string,string|number|boolean|undefined>) {
  return Object.entries(p).filter(([,v]) => v !== undefined)
    .map(([k,v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join("&");
}

export async function evmSwapBase(params: SwapParams) {
  const rpc = process.env.EVM_RPC_URL!;
  const pk  = process.env.EVM_PRIVATE_KEY!;
  const aff = process.env.ZEROX_AFFILIATE || "janus";
  const bps = params.slippageBps ?? Number(process.env.ZEROX_SLIPPAGE_BPS || 50);
  const zeroX = process.env.ZEROX_API_URL || "https://base.api.0x.org";

  const provider = new ethers.JsonRpcProvider(rpc);
  const wallet   = new ethers.Wallet(pk, provider);
  const taker    = params.taker || await wallet.getAddress();

  // 1) Cota/rota 0x
  const qs = toQuery({
    sellToken: params.sellToken,
    buyToken: params.buyToken,
    sellAmount: params.amount,
    takerAddress: taker,
    slippagePercentage: bps / 10_000,
    affiliateAddress: aff,
    enableSlippageProtection: true
  });

  const { data: quote } = await axios.get(`${zeroX}/swap/v1/quote?${qs}`, { timeout: 12_000 });

  // 2) Se token é ERC20, aprovar (se necessário)
  if (quote.allowanceTarget && quote.sellTokenAddress) {
    const erc20 = new ethers.Contract(
      quote.sellTokenAddress,
      [
        "function allowance(address owner,address spender) view returns (uint256)",
        "function approve(address spender,uint256 amount) returns (bool)"
      ],
      wallet
    );
    const allowance: bigint = await erc20.allowance(taker, quote.allowanceTarget);
    const sellAmount = BigInt(quote.sellAmount);
    if (allowance < sellAmount) {
      const txApprove = await erc20.approve(quote.allowanceTarget, sellAmount);
      await txApprove.wait();
    }
  }

  // 3) Enviar transação do swap
  const tx = await wallet.sendTransaction({
    to: quote.to,
    data: quote.data,
    value: quote.value ? BigInt(quote.value) : 0n,
    gasLimit: quote.gas ? BigInt(quote.gas) : undefined
  });
  const receipt = await tx.wait();

  return {
    chain: "base",
    txHash: receipt?.hash || tx.hash,
    buyAmount: quote.buyAmount,
    buyTokenAddress: quote.buyTokenAddress,
    sellAmount: quote.sellAmount,
    sellTokenAddress: quote.sellTokenAddress
  };
}
