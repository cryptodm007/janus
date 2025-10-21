# Janus Automation Engine (n8n)

Instância n8n self-host para orquestrar fluxos **Web2 ↔ Web3** usando os nodes do pacote `@janus/automation-nodes`.

## Estrutura

- Carrega o pacote de nodes compilado (dist) em `/custom/@janus/automation-nodes`.
- Usa variáveis de ambiente para credenciais RPC e chaves (EVM e Solana).
- Workflows de exemplo em `./workflows/`.

## Pré-requisitos

- Docker e Docker Compose
- O pacote `@janus/automation-nodes` **já buildado**:
  ```bash
  pnpm --filter @janus/automation-nodes build
