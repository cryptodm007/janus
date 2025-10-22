import axios from "axios";

const HUB = process.env.AI_HUB_URL || "http://localhost:7331";
const SECRET = process.env.JANUS_MCP_SECRET || "dev-secret";
function sign(body: string) {
  const crypto = require("crypto");
  return crypto.createHmac("sha256", SECRET).update(body).digest("hex");
}

async function mcp(tool: string, input: any) {
  const payload = JSON.stringify({ tool, input, ts: Date.now() });
  const sig = sign(payload);
  const { data } = await axios.post(HUB, { tool, input, ts: Date.now(), sig });
  return data.result || data;
}

async function maybeSwap() {
  // Sinal simples fictício (ex.: threshold de delta)
  const delta = Math.random() * 0.1 - 0.05; // -5%..+5%
  if (delta > 0.03) {
    const out = await mcp("janus.executeNode", {
      node: "bridge.swap",
      params: { from: "USDC", to: "SOL", amount: 100 }
    });
    console.log("[TRADE-AGENT] swap executed", out);
  } else {
    console.log("[TRADE-AGENT] no-op (delta=", delta.toFixed(3), ")");
  }
}

setInterval(maybeSwap, Number(process.env.TRADE_AGENT_INTERVAL_MS || 20000));
maybeSwap().catch(e => console.error(e));
