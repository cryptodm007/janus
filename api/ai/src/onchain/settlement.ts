import { ethers } from "ethers";
import TaskSettlementAbi from "./abi/TaskSettlement.json" assert { type: "json" };

export type TaskClose = {
  taskIdHex: string;  // bytes32 (0x...)
  agent: string;      // address EVM do agente
  amountWei: string;  // em JNS (wei)
};

export async function closeTaskOnChain(input: TaskClose) {
  const rpc = process.env.EVM_RPC_URL!;
  const pk  = process.env.EVM_PRIVATE_KEY!;
  const settlementAddr = process.env.TASK_SETTLEMENT_ADDRESS!;
  const provider = new ethers.JsonRpcProvider(rpc);
  const wallet   = new ethers.Wallet(pk, provider);

  const settlement = new ethers.Contract(settlementAddr, TaskSettlementAbi, wallet);
  const tx = await settlement.closeTask(input.taskIdHex, input.agent, input.amountWei);
  const rc = await tx.wait();
  return { txHash: rc?.hash || tx.hash };
}
