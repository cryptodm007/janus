import express from "express";
import bodyParser from "body-parser";
import { auth } from "./middleware/auth.js";
import { limiter } from "./middleware/limits.js";
import actions from "./routes/actions.js";
import agents from "./routes/agents.js";
import { metricsText, inc } from "../../telemetry/prometheus.js";
import policies from "../../config/policies.json" assert { type: "json" };

const app = express();

// body limit
app.use(bodyParser.json({ limit: (policies.api?.requestMaxBytes ?? 262144) + "b" }));

// headers básicos de segurança
app.disable("x-powered-by");
app.use((_req, res, next) => {
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("Referrer-Policy", "no-referrer");
  next();
});

// health e metrics sem auth
app.get("/health", (_req, res) => res.json({ ok: true, ts: Date.now() }));
app.get("/metrics", (_req, res) => {
  res.setHeader("content-type", "text/plain; version=0.0.4");
  res.send(metricsText());
});

// rate-limit global e auth para rotas AI
app.use(limiter);
app.use("/ai/actions", auth, actions);
app.use("/ai/agents", auth, agents);

// default 404
app.use((_req, res) => res.status(404).json({ error: "not found" }));

const PORT = Number(process.env.AI_API_PORT || 7440);
app.listen(PORT, () => console.log(`[AI-API] listening :${PORT}`));
