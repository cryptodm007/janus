# Janus Protocol Monorepo

**Version:** v0.1.0-alpha • **Date:** 2025-10-20

Janus é um **monorepo** para o Protocolo Janus (MCP verificável on-chain) rodando sobre a ponte **Base–Solana** (testnets: Base Sepolia ↔ Solana Devnet).

> Fase 0 — _Bootstrap do repositório_: estrutura de pastas, governança de contribuição, CI básico e esqueleto de pacotes/apps.

## Requisitos
- Node.js ≥ 20, pnpm ≥ 9 (`npm i -g pnpm`)
- Git ≥ 2.40
- (Opcional) Docker ≥ 24
- (Opcional) Foundry para contratos (`curl -L https://foundry.paradigm.xyz | bash`)

## Setup rápido
```bash
pnpm i
pnpm -w build
```

## Workspaces
- `apps/` — serviços (gateway, docs)
- `packages/` — SDKs, spec, adapters, shared
- `contracts/` — Executor/Registry (Base Sepolia)
- `examples/` — exemplos ponta-a-ponta
- `ops/` — ambientes/devops
- `vendor/` — dependências externas como submódulos (ponte Base–Solana)

## Submódulo (ponte Base–Solana)
> Este repositório **não** traz o submódulo inicializado por padrão dentro do ZIP.
Para adicionar manualmente:
```bash
git submodule add https://github.com/cryptodm007/Bridge-Base-Solana vendor/bridge-base-solana
git submodule update --init --recursive
```

## Branching & Releases
- `main` — estável
- `dev` — integração
- `feat/*`, `fix/*`, `docs/*`, `rfc/*`

Releases seguem **semver**. Primeira tag: `v0.1.0-alpha`.

## Licença
Apache-2.0
