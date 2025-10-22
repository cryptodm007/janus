import { Request, Response, NextFunction } from "express";
import { createHmac, timingSafeEqual } from "crypto";
import policies from "../../../config/policies.json" assert { type: "json" };

function bad(res: Response, code = 401, msg = "unauthorized") {
  return res.status(code).json({ error: msg });
}

export function auth(req: Request, res: Response, next: NextFunction) {
  const apiKey = process.env.JANUS_API_KEY || "dev";
  const got = req.header("x-janus-key");
  if (!got || got !== apiKey) return bad(res);

  // HMAC opcional (recomendado para produção)
  const sig = req.header("x-janus-sig");
  const ts = Number(req.header("x-janus-ts") || 0);
  if (sig) {
    const now = Date.now();
    const windowMs = policies.api?.replayWindowMs ?? 300000;
    if (Math.abs(now - ts) > windowMs) return bad(res, 401, "stale timestamp");

    const raw = JSON.stringify(req.body || {});
    const mac = createHmac("sha256", apiKey).update(`${ts}.${raw}`).digest();
    const gotBuf = Buffer.from(sig, "hex");
    if (gotBuf.length !== mac.length || !timingSafeEqual(gotBuf, mac)) return bad(res);
  }
  next();
}
