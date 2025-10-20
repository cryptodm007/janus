# @janus/adapter-base-solana (Fase 2)

Adapter/driver para a ponte **Base–Solana**. 
Nesta fase, expõe uma API mínima para:
- `sendMessage()` — envia a mensagem arbitrária (direção Base→Solana ou Solana→Base)
- `awaitProveAndFinalize()` — orquestra a etapa de prova/finalização quando necessário
- `getStatus()` — status simplificado do envio

> Integração real com `vendor/bridge-base-solana` será feita conectando os scripts/SDK do submódulo. Por ora, funções são *stubs* seguras para desenvolvimento do Gateway.
