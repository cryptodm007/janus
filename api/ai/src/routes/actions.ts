import { Router } from "express";
import type { ExecuteNodeBody } from "../types.js";
import { resolveNode } from "../nodes/registry.js";
import { closeTaskOnChain } from "../onchain/settlement.js";
import { randomBytes } from "crypto";

const r = Router();

r.post("/execute", async (req, res) => {
  try {
    const body = req.body as ExecuteNodeBody;
    if (!body?.node) return res.status(400).json({ error: "node is required" });

    // executa node
    const fn = resolveNode(body.node);
    const result = await fn(body.params || {});
    const taskId = "task_" + Date.now();

    // liquidação on-chain (DEMO): converte taskId em bytes32 previsível + recompensa fixa
    const taskIdHex = "0x" + randomBytes(32).toString("hex");
    const agent = (body as any).agent || process.env.TASK_VERIFIER_ADDRESS || "0x0000000000000000000000000000000000000000";
    const amountWei = (10n ** 18n).toString(); // 1 JNS – ajuste sua política

    let settleTx: { txHash?: string } | undefined;
    try {
      settleTx = await closeTaskOnChain({ taskIdHex, agent, amountWei });
    } catch (e) {
      // Falha de liquidação não pode invalidar a resposta do node; logue e prossiga
      console.error("[SETTLEMENT] erro:", (e as Error).message);
    }

    res.json({ taskId, status: "completed", node: body.node, result, settlement: settleTx });
  } catch (e: any) {
    res.status(500).json({ error: e.message || "internal" });
  }
});

export default r;
