# @janus/bridge-cli

CLI fino para integrar o adapter com a ponte Base–Solana quando o submódulo não expõe CLIs próprios.

Comandos aceitos:
- Base: `init`, `status`
- Solana: `prove`, `finalize`, `status`

Formato de saída: JSON (uma linha), ex:
{"intentId":"abc","txId":"0x123","status":"SENT"}
