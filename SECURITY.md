# SECURITY — Janus Protocol

Esta política descreve práticas de segurança para IA Layer (MCP), API AI-to-Action, conectores Web2 e integrações on-chain.

## Princípios
- **Menor privilégio:** chaves e permissões mínimas necessárias.
- **Defesa em camadas:** auth, validação, rate-limit, allowlist, auditoria.
- **Fail-safe:** falhas de liquidação on-chain não devem quebrar a execução do node.
- **Observabilidade:** métricas / logs para detecção de abuso.

## Superfícies de Ataque
1. **API AI-to-Action** (`api/ai`) — autenticação, validação, custo, liquidação.
2. **MCP Server** (`ai/mcp/server`) — ferramentas, assinatura HMAC, tamanho de payload, replay.
3. **Connectores Web2** — credenciais (Google, AWS, Stripe).
4. **On-chain** — chaves (EVM/Solana), rotas DEX, liquidação (TaskSettlement).
5. **Prompt Injection** — políticas e sandbox de tools.

## Controles Implementados (Fase 5)
- **HMAC + API Key** (timestamp e janela anti-replay).
- **Rate-limit** por IP/chave.
- **Zod validation** para inputs de rotas e tools MCP.
- **Allowlist** de nodes/tools; **denylist** opcional.
- **Limites de payload** (JSON) e **máximo de ferramentas por requisição**.
- **Custo Máximo por Execução** (limite configurável) e _circuit breaker_ local.
- **Logs e métricas** (Prometheus).
- **Varredura de segredos** (Gitleaks) e **Dependabot**.
- **Threat model** e política de _prompt injection_.

## Relato de Vulnerabilidades
Envie um email para security@janus.example com detalhes técnicos, PoC, impacto e steps de reprodução. Daremos retorno em até 72h.
