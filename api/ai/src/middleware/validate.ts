import { z } from "zod";
import { Request, Response, NextFunction } from "express";
import policies from "../../../config/policies.json" assert { type: "json" };
import { inc } from "../../../telemetry/prometheus.js";

export const ExecuteSchema = z.object({
  node: z.string(),
  params: z.record(z.any()).default({}),
  agent: z.string().optional()
});

export function validateExecute(req: Request, res: Response, next: NextFunction) {
  const maxBytes = policies.api?.requestMaxBytes ?? 262144;
  const cl = Number(req.header("content-length") || 0);
  if (cl > maxBytes) {
    inc("security_reject_total");
    return res.status(413).json({ error: "payload too large" });
  }

  const parsed = ExecuteSchema.safeParse(req.body);
  if (!parsed.success) {
    inc("security_reject_total");
    return res.status(400).json({ error: "invalid input", details: parsed.error.flatten() });
  }

  // allowlist
  const node = parsed.data.node;
  const allow = new Set<string>(policies.api?.nodesAllowlist || []);
  if (!allow.has(node)) {
    inc("security_reject_total");
    return res.status(403).json({ error: "node not allowed" });
  }

  // injeta corpo validado
  (req as any).__exec = parsed.data;
  next();
}
