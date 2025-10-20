# @janus/adapter-base-solana — Fase 2b (ligado ao submódulo)

Este adapter agora **se integra** ao repositório da ponte Base–Solana via **CLI** configurável.
Ele executa comandos do submódulo `vendor/bridge-base-solana` (que você adicionou no monorepo).

## O que ele faz
- `sendMessage()` → inicia o fluxo de **mensagem arbitrária** na direção escolhida
- `awaitProveAndFinalize()` → para **Base→Solana**, faz polling (prove/finalize) até concluir
- `getStatus()` → consulta estado pelo `intentId` (se o CLI suportar)

> Observação: como o repositório da ponte ainda está em evolução e não padroniza um único binário,
> tornamos os comandos **configuráveis via .env**. Você aponta para os scripts/CLIs reais do submódulo.

---

## Variáveis de ambiente necessárias (no **root** do monorepo ou no serviço que chama o adapter)

Crie/atualize um arquivo `.env` (ou use os secrets da sua plataforma) com:

```
# Caminhos para os CLIs (ajuste conforme o submódulo vendor/bridge-base-solana)
BRIDGE_BASE_CLI="node vendor/bridge-base-solana/base/cli.js"
BRIDGE_SOLANA_CLI="node vendor/bridge-base-solana/solana/cli.js"

# Redes alvo (ex.: Base Sepolia / Solana Devnet)
BRIDGE_BASE_NETWORK="sepolia"
BRIDGE_SOLANA_NETWORK="devnet"

# Ajustes de tempo
ADAPTER_MAX_WAIT_MS=900000   # ~15 min padrão
ADAPTER_POLL_MS=5000         # 5s entre polls

# (Opcional) Pasta de trabalho onde ficam configs/keys da ponte
BRIDGE_WORKDIR="vendor/bridge-base-solana"
```

> Dica: Se o CLI for via `bash` ao invés de `node`, use:  
> `BRIDGE_BASE_CLI="bash vendor/bridge-base-solana/base/scripts.sh"`

---

## Como mapear para o repositório da ponte

O adapter espera que o CLI aceite **subcomandos**:

- `init` — inicia a mensagem arbitrária (retorna um `intentId`/`txId`)
- `prove` — etapa de prova (Base→Solana)
- `finalize` — etapa de finalização (Base→Solana)
- `status` — (opcional) retorna estado atual pelo `intentId`

Exemplo (direção Base→Solana):

```bash
$ {{BRIDGE_BASE_CLI}} init --network {{BRIDGE_BASE_NETWORK}} --payload base64:<...>
# saída esperada (JSON):
# {{ "intentId": "abc123", "txId": "0x...", "status": "SENT" }}

# depois de ~15min, o merkle root é postado em Solana.
$ {{BRIDGE_SOLANA_CLI}} prove --network {{BRIDGE_SOLANA_NETWORK}} --intent abc123
$ {{BRIDGE_SOLANA_CLI}} finalize --network {{BRIDGE_SOLANA_NETWORK}} --intent abc123
```

> Se o CLI do submódulo usar outros nomes/parametrizações, **ajuste os scripts do CLI** ou crie *wrappers*.
> O adapter apenas invoca os comandos com os parâmetros que você define.

---

## API do adapter (TypeScript)

```ts
type Direction = 'BASE_TO_SOLANA' | 'SOLANA_TO_BASE';

interface SendMessageParams { direction: Direction; payload: Uint8Array | string; intentId?: string; timeoutMs?: number; }
interface MessageReceipt { intentId?: string; txId?: string; status: 'QUEUED'|'SENT'|'PROVEN'|'FINALIZED'|'EXECUTED'|'REJECTED'; error?: string; }

sendMessage(params): Promise<MessageReceipt>
awaitProveAndFinalize(intentId, opts?): Promise<MessageReceipt>
getStatus(intentId): Promise<MessageReceipt>
```

---

## Exemplo de uso (no Gateway)

O `apps/gateway/src/index.ts` já chama:

```ts
const direction = env.chain.origin === 'Base' ? 'BASE_TO_SOLANA' : 'SOLANA_TO_BASE';
const payload = Buffer.from(JSON.stringify(env), 'utf-8');
const send = await sendMessage({ direction, payload, intentId: env.id });
if (direction === 'BASE_TO_SOLANA') {
  const fin = await awaitProveAndFinalize(env.id, { maxWaitMs: MAX_WAIT_MS, pollMs: POLL_MS });
}
```

---

## Segurança e boas práticas
- **Nunca** coloque chaves privadas do deploy no repo. Use `.env`/secrets.
- Logue somente metadados (sem payloads sensíveis).
- Trate `timeout`/`retries` e **idempotência** (o adapter já aplica backoff).
- Em produção, adicione auditoria e circuit breakers no Executor.
