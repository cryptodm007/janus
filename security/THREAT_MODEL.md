# Threat Model — Janus

## Atacantes
- **Abusador de API** (chave comprometida).
- **Agente malicioso** (prompt injection, tool abuse).
- **Man-in-the-middle** (sem TLS).
- **Exfiltração de segredos** (CI/CD, logs).
- **On-chain griefing** (liquidações indevidas).

## Ativos
- Chaves EVM/Solana; STRIPE/Google/AWS.
- Tokens JNS (recompensas).
- Dados de usuários (Sheets/S3).

## Vetores & Mitigações
1) **Replay** — HMAC + `ts` com janela (5 min) e cache de nonce.
2) **Flood** — Rate-limit global + por chave.
3) **Prompt Injection** — sandbox e allowlist, entrada neutra, limpeza de contexto.
4) **Gastança** — `MAX_COST_USD` e _circuit breaker_.
5) **Exposição** — logs sem dados sensíveis, segregação .env, secret manager (futuro).
