# RFC-0001 — MCP-Janus Envelope

## Objetivo
Permitir que mensagens MCP sejam **executáveis on-chain** de forma determinística por agentes Janus, usando uma ponte L1/L2 (Base ↔ Solana) e um Executor com políticas (constituição, caps, nonces, deadlines).

## Envelope
```json
{
  "type": "request",
  "id": "string",
  "method": "string",
  "params": {},
  "chain": {
    "origin": "Base|Solana",
    "destination": "Base|Solana",
    "executor": "0x....",
    "signature": "0x...",
    "constitution": "ipfs://... (opcional)",
    "nonce": "0x... (opcional)",
    "deadline": 0
  }
}
