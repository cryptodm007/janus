# Janus AI Layer (MCP)
Camada MCP que expõe o Janus como ferramentas para agentes de IA.

## Conceito
- Agentes (Claude/ChatGPT/LangChain/Autogen) chamam o Janus via MCP.
- O Janus executa ações Web2↔Web3, devolve recibos e telemetria.

## Rodando local
```bash
pnpm i
pnpm --filter @janus/mcp-server dev
