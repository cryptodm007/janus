# Janus Protocol

## Visão Geral  
O Janus Protocol é uma arquitetura de sincronização e confirmação cross-chain de eventos entre cadeias EVM-like e Solana.  
O fluxo básico é:

1. **Listeners** (Base / Solana) escutam logs ou slots e emitem eventos `CHAIN_HEAD` e `BRIDGE_MESSAGE` / `AGENT_SIGNAL`.  
2. Um **Router** normaliza e encaminha eventos para a **Fila Persistente**.  
3. A **Job Queue** aplica **rate limiting**, **backpressure**, e persiste jobs (SQLite ou Redis).  
4. O **AISyncManager** lê eventos, aplica transformação/estado (agents, transfers, bridge messages) e confirma com base em finality (head-based).  
5. Infraestrutura de **telemetria**, **tracing**, **locks distribuídos**, **backfill histórico**, e **Admin API** suportam operação confiável.

## Estrutura de Pastas  
- `core/` — esquemas, interfaces, state store, locks fallback.  
- `bridge/` — providers, listeners, decoders, historical scanner.  
- `services/` — queue manager, sync manager, job orchestration.  
- `storage/` — backends de fila (SQLite, Redis).  
- `locks/` — factory de locks, redis fencing lock.  
- `rate/` — rate limiter e backpressure.  
- `resilience/` — circuit breaker, adaptive polling.  
- `replay/` — serviços de replay histórico e endpoints admin.  
- `telemetry/` — métricas Prometheus, tracing setup.  
- `config/` — arquivo `sync.yaml`, `.env` exemplo.  
- `tests/` — unit e integration tests.  
- `bootstrap_sync.py` — script de bootstrap.  
- `CHANGELOG.md`, `pyproject.toml`, `README.md`.

## Instalação Rápida  
```bash
git clone https://github.com/janus-protocol/janus.git  
cd janus  
pip install -r requirements.txt  
cp .env.example .env   # configurar BASE_WS_ENDPOINT, SOLANA_WS_ENDPOINT, REDIS_URL, JANUS_ADMIN_TOKEN  
