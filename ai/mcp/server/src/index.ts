import http from "http";
import { createHmac } from "crypto";
import { executeNode } from "./tools/janus.executeNode.js";
import { readSheet } from "./tools/janus.gsheets.read.js";
import { s3PutObject } from "./tools/janus.s3.put.js";
import { stripeCharge } from "./tools/janus.stripe.charge.js";
import { metricsText, inc } from "../../../../telemetry/prometheus.js";

const PORT = Number(process.env.MCP_PORT || 7331);
const SECRET = process.env.JANUS_MCP_SECRET || "dev-secret";

type MCPRequest = { tool: string; input: unknown; ts?: number; sig?: string };

function verifySig(body: string, sig?: string) {
  const h = createHmac("sha256", SECRET).update(body).digest("hex");
  return sig === h;
}

const tools: Record<string, (input: any) => Promise<any>> = {
  "janus.executeNode": executeNode,
  "janus.gsheets.read": readSheet,
  "janus.s3.put": s3PutObject,
  "janus.stripe.charge": stripeCharge
};

const server = http.createServer(async (req, res) => {
  try {
    // /metrics
    if (req.method === "GET" && req.url === "/metrics") {
      res.writeHead(200, { "content-type": "text/plain; version=0.0.4" });
      res.end(metricsText());
      return;
    }

    if (req.method !== "POST") {
      res.writeHead(405).end();
      return;
    }

    const chunks: Buffer[] = [];
    for await (const c of req) chunks.push(c as Buffer);
    const body = Buffer.concat(chunks).toString("utf8");
    const data = JSON.parse(body) as MCPRequest;

    if (!verifySig(body, data.sig)) {
      res.writeHead(401).end(JSON.stringify({ error: "bad signature" }));
      return;
    }

    const fn = tools[data.tool];
    if (!fn) {
      res.writeHead(404).end(JSON.stringify({ error: "tool not found" }));
      return;
    }

    inc("ai_tasks_total");
    const out = await fn(data.input);
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ ok: true, result: out }));
  } catch (e: any) {
    // em produção, separar counters de erro por tool
    res.writeHead(500).end(JSON.stringify({ error: e.message || "internal" }));
  }
});

server.listen(PORT, () => {
  console.log(`[MCP] listening at :${PORT}`);
});
