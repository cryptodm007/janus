# Janus Gateway — Fase 2

API HTTP para traduzir mensagens **MCP → MCP-Janus**, validar,
e enviar para execução via **ponte Base–Solana**.

**Nesta fase**:
- Endpoint `POST /mcp/intent`
- `GET /healthz` e `GET /metrics` (placeholder)
- Integração com `@janus/adapter-base-solana` (stub)
- Carrega configuração via `.env`

## Rodar localmente
```bash
pnpm i
pnpm --filter @janus/gateway dev
```
ou
```bash
cd apps/gateway
pnpm i
pnpm dev
```

## Variáveis de ambiente (.env)
Veja `apps/gateway/.env.example` e crie `apps/gateway/.env` com valores reais no seu ambiente.
