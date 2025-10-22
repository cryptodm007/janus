import { Router } from "express";
import type { ExecuteNodeBody } from "../types.js";
import { resolveNode } from "../nodes/registry.js";

const r = Router();

r.post("/execute", async (req, res) => {
  try {
    const body = req.body as ExecuteNodeBody;
    if (!body?.node) return res.status(400).json({ error: "node is required" });

    const fn = resolveNode(body.node);
    const result = await fn(body.params || {});
    const taskId = `task_${Date.now()}`;

    res.json({ taskId, status: "completed", node: body.node, result });
  } catch (e: any) {
    res.status(500).json({ error: e.message || "internal" });
  }
});

export default r;
