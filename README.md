# 🧬 JANUS PROTOCOL  
**Where Agents Think, Chains Act.**

---

## 🌐 Visão Geral

O **Janus Protocol** é uma infraestrutura modular que conecta **IA ↔ Web2 ↔ Web3**.  
Ele permite que agentes de inteligência artificial executem ações reais em aplicações Web2 (Google Sheets, AWS S3, Stripe etc.) e interajam diretamente com contratos inteligentes em redes como **Base** e **Solana**.

> A IA cria a intenção.  
> O Janus executa.  
> A blockchain valida.

---

## ⚙️ Arquitetura

```plaintext
           ┌───────────────────────────────┐
           │         IA Layer (MCP)        │
           │  • Servidor MCP               │
           │  • Agentes Autônomos (JNS)    │
           │  • Economia & Staking         │
           └──────────────┬────────────────┘
                          │  JSON / HMAC / MCP
           ┌──────────────▼────────────────┐
           │         Janus Core            │
           │  • Orquestrador de Nodes      │
           │  • Bridge Base ↔ Solana       │
           │  • Connectores Web2           │
           └──────────────┬────────────────┘
                          │  RPC / Tx / Events
           ┌──────────────▼────────────────┐
           │   Blockchains (Base, Solana)  │
           │   • Contratos de Agentes      │
           │   • Liquidação de Tarefas     │
           └───────────────────────────────┘
```

---

## 📦 Estrutura de Pastas

| Diretório | Descrição |
|------------|------------|
| `ai/mcp/` | Servidor MCP e ferramentas usadas por agentes. |
| `ai/registry/` | Registro de agentes e ferramentas (off-chain). |
| `ai/mcp/agents/` | Exemplos de agentes (trade-agent, data-agent). |
| `api/ai/` | API HTTP para receber ações cognitivas e executar nodes. |
| `core/` | Motor central de execução e fila de tarefas. |
| `services/bridge/` | Bridge Base ↔ Solana + integrações DEX (0x / Jupiter). |
| `packages/connectors/` | Conectores Web2 (Google Sheets, AWS S3, Stripe). |
| `contracts/` | Smart contracts (JNS – Registry, Staking, Rewards, Settlement). |
| `telemetry/` | Métricas, Prometheus, Grafana dashboards. |
| `config/` | Políticas de segurança, rate-limits, allowlists. |
| `.github/` | Workflows de CI/CD, scans de segurança. |

---

## 🚀 Quick Start (Dev Env)

```bash
# 1) instalar dependências
pnpm install

# 2) configurar variáveis
cp .env.example .env
# (editar chaves API / RPC)

# 3) subir AI API + MCP Server
pnpm --filter @janus/ai-api dev
pnpm --filter @janus/mcp-server dev

# 4) executar agente exemplo
pnpm --filter @janus/data-agent dev
```

Endpoints principais:  
- **AI API:** `http://localhost:7440`  
- **MCP Server:** `http://localhost:7331`  
- **Métricas Prometheus:** `/metrics`  
- **Healthcheck:** `/health`

---

## 🤖 Camada de IA (MCP + Agentes)

A **IA Layer** transforma o Janus em um **Hub cognitivo** para agentes.

- **Servidor MCP** → expõe ferramentas (`janus.executeNode`, `janus.gsheets.read`, `janus.s3.put`, `janus.stripe.charge`).  
- **Agentes** → instâncias autônomas que rodam scripts (TypeScript/Python) e executam ações via MCP.  
- **Economia JNS** → cada agente é registrado on-chain, com stake e recompensas automáticas.

**Exemplo de fluxo (Data Agent):**

1. Lê uma planilha do Google Sheets  
2. Grava JSON no AWS S3  
3. Registra o hash on-chain  
4. Recebe recompensa JNS via `TaskSettlement`

---

## 🌉 Bridge Base ↔ Solana

O **Janus Bridge** é responsável por orquestrar trocas e mensagens cross-chain.  
Atualmente implementa:

- **Swaps EVM (Base)** → via [0x Swap API](https://0x.org/docs).  
- **Swaps Solana** → via [Jupiter Aggregator](https://jup.ag).  
- **Liquidação on-chain** → integração com contrato `TaskSettlement.sol`.

---

## 💾 Conectores (Web2 First-Class)

| Conector | Ação | Descrição |
|-----------|------|-----------|
| `google/sheets` | read / append | Interage com planilhas Google. |
| `aws/s3` | put / get | Armazena ou lê objetos S3. |
| `stripe/payments` | charge / refund | Cria ou reverte cobranças. |

Todos são **assincrônicos, com retry + timeout**, e utilizam credenciais via `.env`.

---

## 🧠 Economia JNS (on-chain)

| Contrato | Função |
|-----------|--------|
| `AgentRegistry` | NFT de identidade do agente. |
| `AgentStaking` | Stake / slashing em JNS. |
| `AgentRewards` | Pagamentos de tarefas concluídas. |
| `TaskSettlement` | Liquidação de tarefas e emissão de recompensas. |

Deploys demo estão em Base Sepolia / Solana Devnet.

---

## 🔒 Segurança (Fase 5)

| Controle | Implementação |
|-----------|---------------|
| Autenticação HMAC | Headers `x-janus-key`, `x-janus-sig`, `x-janus-ts` |
| Anti-replay | Janela 5 min + verificação HMAC |
| Rate-Limit | Express-Rate-Limit (600 req/min por chave) |
| Validação | Zod Schemas + Allowlist de Nodes/Tools |
| Circuit Breaker | Abre em ≥ 50 % falhas últimas 20 requisições |
| Cost Cap | Máximo USD por ação (5 USD padrão) |
| Scanners | Gitleaks + Semgrep + Dependabot (CI) |
| Políticas | `config/policies.json` e `docs/security/*` |

Logs e métricas expõem contadores:
```
ai_tasks_total
ai_tasks_success_total
onchain_settlement_total
security_reject_total
rate_limit_drops_total
```

---

## 📊 Observabilidade

- **Prometheus Exporter** embutido em API e MCP.  
- **Dashboard Grafana**: `telemetry/ai/dashboards/grafana.json`.  
- **Logs Estruturados** (JSON, UTC).  
- **Healthcheck** → `/health`.

---

## 🤝 Contribuindo

Consulte [`CONTRIBUTING.md`](./CONTRIBUTING.md).  
Pull Requests devem seguir Conventional Commits e passar nos tests e scans.

---

## 🧩 Ecossistema em Expansão

| Módulo | Status |
|---------|--------|
| **Janus MCP** | ✅ ativo |
| **AI API** | ✅ ativo |
| **Bridge Base ↔ Solana** | 🧪 testnet |
| **Conectores Web2** | ✅ Sheets/S3/Stripe |
| **Economia JNS** | 🧱 on-chain beta |
| **Observabilidade** | ✅ Prometheus / Grafana |
| **Hardening & Security** | ✅ Fase 5 completa |

---

## 🪙 Licença
MIT © Janus Protocol – Construindo a infraestrutura da Internet Cognitiva.

> *O Janus nasceu para ser a ponte entre a lógica da IA e a confiança da blockchain.*
