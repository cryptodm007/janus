# MCP @ Janus — Especificação de Ferramentas

## Autenticação
- Header: `x-janus-key: <API_KEY>`
- Assinatura HMAC opcional (corpo inteiro) — ver `ai/mcp/server/src/index.ts`

## Tools
### janus.executeNode
```json
{ "tool": "janus.executeNode", "input": { "node": "bridge.swap", "params": { "from": "USDC", "to": "SOL", "amount": 100 } }, "sig": "<HMAC>" }
