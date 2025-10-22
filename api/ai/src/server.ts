import express from "express";
import bodyParser from "body-parser";
import { auth } from "./middleware/auth.js";
import actions from "./routes/actions.js";
import agents from "./routes/agents.js";
import { metricsText, inc } from "../../telemetry/prometheus.js";

const app = express();
app.use(bodyParser.json());

// exposição de métricas
app.get("/metrics", (_req, res) => {
  res.setHeader("content-type", "text/plain; version=0.0.4");
  res.send(metricsText());
});

// middleware para contar requisições AI (exemplo)
app.use((_req, _res, next) => { inc("ai_tasks_total"); next(); });

app.use("/ai/actions", auth, actions);
app.use("/ai/agents", auth, agents);

const PORT = Number(process.env.AI_API_PORT || 7440);
app.listen(PORT, () => console.log(`[AI-API] listening :${PORT}`));
