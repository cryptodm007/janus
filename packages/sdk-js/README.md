# @janus/sdk-js

Cliente para o Janus Gateway.

## Uso
```ts
import { JanusClient } from '@janus/sdk-js';

const client = new JanusClient({ baseURL: 'http://localhost:8080' });

const env = {
  type: 'request',
  id: 'abc123',
  method: 'call_tool',
  params: { name: 'swap', arguments: { tokenIn: 'USDC', tokenOut: 'SOL', amount: '100' } },
  chain: { origin: 'Base', destination: 'Solana', executor: '0xExecutor', signature: '0xSIG', deadline: Math.floor(Date.now()/1000)+3600 }
};

const sent = await client.sendIntent(env);
if (sent.ok && sent.id) {
  const fin = await client.awaitResult(sent.id);
  console.log(fin);
}
