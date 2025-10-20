
### 1.2 Criar `examples/mcp-claude-demo/demo.mjs`
`examples/mcp-claude-demo/demo.mjs`
```js
import { JanusClient } from '../../packages/sdk-js/dist/index.js';

const client = new JanusClient({ baseURL: process.env.JANUS_GATEWAY_URL || 'http://localhost:8080' });

// Envelope de exemplo (ajuste os campos para seu caso)
const env = {
  type: 'request',
  id: 'demo-' + Date.now(),
  method: 'call_tool',
  params: { name: 'swap', arguments: { tokenIn: 'USDC', tokenOut: 'SOL', amount: '100' } },
  chain: {
    origin: 'Base',
    destination: 'Solana',
    executor: '0x0000000000000000000000000000000000000000',
    signature: '0xSIG',
    deadline: Math.floor(Date.now() / 1000) + 3600
  }
};

console.log('Sending intent:', env.id);
const sent = await client.sendIntent(env);
console.log('sendIntent:', sent);

if (sent.ok && sent.id) {
  const fin = await client.awaitResult(sent.id, { maxWaitMs: 60_000, pollMs: 3_000 });
  console.log('awaitResult:', fin);
} else {
  console.error('Failed to send intent:', sent);
}
