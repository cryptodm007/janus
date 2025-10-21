# @janus/automation-nodes

Custom nodes do n8n para integrar **Web2 → Web3** no Janus Protocol.

## Nodes incluídos
- **BaseTransactionBuilder** (EVM – Base)
- **BaseTransactionExecutor** (EVM – Base)
- **SolanaTransactionBuilder**
- **SolanaTransactionExecutor**
- **OnChainEventTrigger** (EVM + Solana)

## Como usar no n8n (self-host)
1. `pnpm i && pnpm build`
2. Copie a pasta `dist` para a pasta de custom nodes do n8n **ou** publique como pacote e instale no container do n8n.
3. Configure as credenciais via variáveis de ambiente do n8n:
   - EVM: `JANUS_EVM_PRIVATE_KEY`, `JANUS_EVM_RPC_WS`, `JANUS_EVM_RPC_HTTP`
   - Solana: `JANUS_SOLANA_SECRET_KEY_BASE58`, `JANUS_SOLANA_RPC_HTTP`
4. Importe os workflows de exemplo em `apps/automation-engine/workflows`.

> **Atenção:** Não exponha chaves privadas no editor do n8n. Prefira secrets/variáveis de ambiente.
