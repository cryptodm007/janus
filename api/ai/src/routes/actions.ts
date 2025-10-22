import { Router } from "express";
import { resolveNode } from "../nodes/registry.js";
import { closeTaskOnChain } from "../onchain/settlement.js";
import { randomBytes } from "crypto";
import { validateExecute } from "../middleware/validate.js";
import { inc } from "../../telemetry/prometheus.js";
import policies from "../../../config/policies.json" assert { type: "json" };

// circuito simples: se >50% falhas em janela de 20, abre
const outcomes: boolean[] = [];
function recordOutcome(ok: boolean) {
  outcomes.push(ok);
  if (outcomes.length > (policies.api?.circuitBreakerWindow ?? 20)) outcomes.shift();
}
function breakerOpen() {
  const win = outcomes.slice(- (policies.api?.circuitBreakerWindow ?? 20));
  if (win.length < 5) return false;
  const fails = win.filter(x => !x).length;
  const ratio = fails / win.length;
  return ratio >= (policies.api?.circuitBreakerFailRatio ?? 0.5);
}

const r = Router();

r.post("/execute", validateExecute, async (req, res) => {
  if (breakerOpen()) {
    inc("circuit_breaker_open_total");
    return res.status(503).json({ error: "circuit open, retry later" });
  }

  try {
    const body = (req as any).__exec as { node: string; params: any; agent?: string };

    // custo máximo (quando aplicável)
    const maxCost = Number(policies.api?.maxCostUsdPerAction ?? 5);
    if (typeof body.params?.estimatedCostUsd === "number" && body.params.estimatedCostUsd > maxCost) {
      inc("security_reject_total");
      return res.status(402).json({ error: "cost exceeds policy", limitUsd: maxCost });
    }

    const fn = resolveNode(body.node);
    const result = await fn(body.params || {});
    const taskId = "task_" + Date.now();

    // liquidação on-chain (melhorar com política por node/resultado)
    const taskIdHex = "0x" + randomBytes(32).toString("hex");
    const agent = body.agent || process.env.TASK_VERIFIER_ADDRESS || "0x0000000000000000000000000000000000000000";
    const amountWei = (10n ** 18n).toString(); // 1 JNS demo

    let settleTx: { txHash?: string } | undefined;
    try {
      settleTx = await closeTaskOnChain({ taskIdHex, agent, amountWei });
      if (settleTx?.txHash) inc("onchain_settlement_total");
    } catch (e) {
      // não falha a requisição por erro de liquidação
      console.error("[SETTLEMENT] erro:", (e as Error).message);
    }

    inc("ai_tasks_success_total");
    recordOutcome(true);
    res.json({ taskId, status: "completed", node: body.node, result, settlement: settleTx });
  } catch (e: any) {
    recordOutcome(false);
    res.status(500).json({ error: e.message || "internal" });
  }
});

export default r;
