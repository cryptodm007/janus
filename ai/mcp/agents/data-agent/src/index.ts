import axios from "axios";

const HUB = process.env.AI_HUB_URL || "http://localhost:7331";
const SECRET = process.env.JANUS_MCP_SECRET || "dev-secret";
function sign(body: string) {
  const crypto = await import("crypto");
  return crypto.createHmac("sha256", SECRET).update(body).digest("hex");
}

async function mcp(tool: string, input: any) {
  const payload = JSON.stringify({ tool, input, ts: Date.now() });
  const sig = await sign(payload);
  const { data } = await axios.post(HUB, { tool, input, ts: Date.now(), sig });
  return data.result || data;
}

async function runOnce() {
  // 1) Lê dados do Sheets
  const rows = await mcp("janus.gsheets.read", {
    spreadsheetId: process.env.DATA_AGENT_SHEET_ID,
    range: process.env.DATA_AGENT_SHEET_RANGE || "A1:C100"
  });

  // 2) Escreve no S3
  await mcp("janus.s3.put", {
    bucket: process.env.DATA_AGENT_BUCKET,
    key: `ingest/${Date.now()}.json`,
    content: JSON.stringify(rows)
  });

  // 3) Cria hash on-chain (via AI API -> node onchain.hashRecord)
  const onchain = await mcp("janus.executeNode", {
    node: "onchain.hashRecord",
    params: { data: rows }
  });

  console.log("[DATA-AGENT] done", onchain);
}

setInterval(runOnce, Number(process.env.DATA_AGENT_INTERVAL_MS || 15000));
runOnce().catch(e => console.error(e));
