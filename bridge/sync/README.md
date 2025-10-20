# Bridge Sync Module (Fase 9)

Módulo de sincronização entre Base e Solana, com validação leve via Proof-of-Relay (PoR).
- `sync_manager.py`: loop de sincronização e mesclagem de estados.
- `relay_proof.py`: consenso PoR para validar blocos/eventos.

## Dependências Internas
- `bridge/vendor/bridge_base_solana` deve expor:
  - `get_base_state() -> dict`
  - `get_solana_state() -> dict`
- `core/state_manager.StateManager` deve expor:
  - `update_state(state: dict) -> None`

## Próximos passos
- Fase 10: AI Relay Validation Layer (validação assistida por IA).
