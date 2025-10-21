# Janus Bridge Adapter (Base ↔ Solana)

Camada de interoperabilidade do Janus Protocol responsável por enviar **mensagens** e **tokens** entre as redes **Base (EVM)** e **Solana**.

### Estrutura
- `interfaces/IBridgeAdapter.sol` → Interface de provedores de ponte.
- `core/JanusRegistry.sol` → Registro, escrow e liquidação cross-chain.
- `libs/Types.sol` → Tipos compartilhados.
- `programs/solana/bridge_adapter` → Programa Anchor do lado Solana.

### Funcionalidades
- Anti-replay de mensagens.
- Verificação de prova (placeholder pronta para acoplamento a providers).
- Callback de liquidação com verificação de prova no EVM.
- Modularidade: múltiplas bridges podem coexistir (governança definirá ativa).

### Roadmap
1. MVP single-chain (Base).
2. Testnet Base↔Solana.
3. Mainnet redundante (duas bridges).
4. Batching e gas sponsorship.

---
