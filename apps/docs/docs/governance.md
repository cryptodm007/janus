# Governança (Testnet)

O `ConstitutionDAO` controla as políticas do `Executor` via **timelock**:
- Proponentes (council) criam propostas (`propose`).
- Após o `delay`, qualquer endereço pode `execute`.

## Fluxo
1. Transferir `ownership` do **Executor** para o `ConstitutionDAO`.
2. Adicionar proponentes: `setProposer(<addr>, true)` (apenas owner do DAO).
3. Codificar a ação:
   - `encodeSetWhitelist(target, allowed)`
   - `encodeSetCap(target, maxValue)`
4. `propose` com `target=Executor`, `value=0`, `data=<encoded>`.
5. Aguardar `delay` → `execute(opId)`.

> Estado: **TESTNET ONLY** (Base Sepolia ↔ Solana Devnet).
