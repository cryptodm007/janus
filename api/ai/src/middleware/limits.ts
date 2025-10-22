import rateLimit from "express-rate-limit";
import policies from "../../../config/policies.json" assert { type: "json" };
import { inc } from "../../../telemetry/prometheus.js";

export const limiter = rateLimit({
  windowMs: 60 * 1000,
  max: policies.api?.rateLimitPerMin ?? 600,
  standardHeaders: true,
  legacyHeaders: false,
  handler: (_req, res) => {
    inc("rate_limit_drops_total");
    res.status(429).json({ error: "rate limit" });
  }
});
