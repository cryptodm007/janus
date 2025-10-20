# Demo — MCP (Claude) → Janus Gateway → Ponte → Executor

Este demo usa o **SDK-JS** para enviar um envelope MCP-Janus ao Gateway e aguardar o resultado (polling).
> Requer o Gateway rodando (porta 8080 por padrão) e variáveis de ambiente configuradas.

## Rodar
```bash
pnpm --filter @janus/sdk-js build
node examples/mcp-claude-demo/demo.mjs
