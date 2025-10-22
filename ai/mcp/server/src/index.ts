import http from "http";
import { createHmac, timingSafeEqual } from "crypto";
import { executeNode } from "./tools/janus.executeNode.js";
import { readSheet } from "./tools/janus.gsheets.read.js";
import { s3PutObject } from "./tools/janus.s3.put.js";
import { stripeCharge } from "./tools/janus.stripe.charge.js";
import { metricsText, inc } from "../../../../telemetry/prometheus.js";
import policies from "../../../../config/policies.json" assert { type: "json" };

const PORT = Number(process.env.MCP_PORT || 7331);
const SECRET = process.env.JANUS_MCP_SECRET || "dev-secret";
const MAX = policies.mcp?.requestMaxBytes ?? 131072;
const WINDOW = policies.mcp?.replayWindowMs ?? 300000;

// allowlist
const ALLOW = new Set<string>(policies.mcp?.toolsAllowlist || []);

type MCPRequest = { tool: string; input: unknown; ts?: number; sig?: string };

function verifySig(body: string, ts: number, sig?: string) {
  if (!sig) return false;
  const mac = createHmac("sha256", SECRET).update(`${ts}.${body}`).digest();
  const got = Buffer.from(sig, "hex");
  return got.length === mac.length && timingSafeEqual(got, mac);
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

    let size = 0;
    const chunks: Buffer[] = [];
    for await (const c of req) {
      size += (c as Buffer).length;
      if (size > MAX) {
        inc("security_reject_total");
        res.writeHead(413).end(JSON.stringify({ error: "payload too large" }));
        return;
      }
      chunks.push(c as Buffer);
    }
    const body = Buffer.concat(chunks).toString("utf8");
    const data = JSON.parse(body) as MCPRequest;

    // timestamp + assinatura
    const now = Date.now();
    if (!data.ts || Math.abs(now - data.ts) > WINDOW || !verifySig(body, data.ts, data.sig)) {
      inc("security_reject_total");
      res.writeHead(401).end(JSON.stringify({ error: "auth failed" }));
      return;
    }

    // allowlist de tools
    if (!ALLOW.has(data.tool)) {
      inc("security_reject_total");
      res.writeHead(403).end(JSON.stringify({ error: "tool not allowed" }));
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
    res.writeHead(500).end(JSON.stringify({ error: e.message || "internal" }));
  }
});

server.listen(PORT, () => {
  console.log(`[MCP] listening at :${PORT}`);
});
