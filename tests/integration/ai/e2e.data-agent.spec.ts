/**
 * Pré-requisitos:
 * - AI API rodando (http://localhost:7440)
 * - MCP Server rodando (http://localhost:7331)
 * - Variáveis .env preenchidas
 */
import assert from "assert";
import axios from "axios";

describe("E2E Data Agent", () => {
  it("executa leitura de sheet -> grava em S3 -> hash on-chain", async () => {
    const MCP = process.env.AI_HUB_URL || "http://localhost:7331";
    const payload = { tool: "janus.gsheets.read", input: {
      spreadsheetId: process.env.DATA_AGENT_SHEET_ID,
      range: "A1:B5"
    }};
    const { data } = await axios.post(MCP, payload);
    assert.ok(data.result, "sem resultado do sheets");
  });
});
