# Janus — Fase 1: Contratos (Executor & Registry)

**Data:** 2025-10-20

Este pacote contém o esqueleto de contratos:
- `Executor.sol`: valida intent MCP‑Janus (assinante/nonce/deadline/caps) e emite eventos.
- `Registry.sol`: registra agentes, chaves e constituições (hash).

Inclui:
- `foundry.toml`
- `src/` com contratos
- `script/Deploy.s.sol` (deploy)
- `test/` com testes básicos

## Requisitos
- Foundry (forge/cast): https://book.getfoundry.sh
- RPC da Base Sepolia (ex.: Alchemy/Ankr/QuickNode)

## Comandos
```bash
forge install foundry-rs/forge-std@v1.9.6 --no-commit
forge fmt
forge build
forge test -vv
```

## Deploy (exemplo)
Crie `.env` com:
```
RPC_URL_BASE_SEPOLIA=...
PRIVATE_KEY=0xSUA_CHAVE_DE_TESTNET
```
# Contratos - Economia de Agentes
- AgentRegistry: identidade (NFT) e metadados
- AgentStaking: stake/slashing em JNS
- AgentRewards: distribuição por tarefa
- TaskSettlement: fechamento de tarefa (assinaturas)

Execute:
```bash
forge script script/Deploy.s.sol:Deploy --rpc-url $RPC_URL_BASE_SEPOLIA --broadcast --private-key $PRIVATE_KEY
```
