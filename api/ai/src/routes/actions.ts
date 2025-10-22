import { Router } from "express";
import type { ExecuteNodeBody } from "../types.js";

// TODO: plugar dispatcher real do Janus Core
async function dispatchExecuteNode(body: ExecuteNodeBody) {
  // Placeholder: aqui você chama services/core com o node solicitado
  return { taskId: `task_${Date.now()}`, status: "queued", node: body.node, params: body.params };
}

const r = Router();

r.post("/execute", async (req, res) => {
  try {
    const body = req.body as ExecuteNodeBody;
    if (!body?.node) return res.status(400).json({ error: "node is required" });
    const out = await dispatchExecuteNode(body);
    res.json(out);
  } catch (e: any) {
    res.status(500).json({ error: e.message || "internal" });
  }
});

export default r;
