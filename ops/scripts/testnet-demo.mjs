import { JanusClient } from '../../packages/sdk-js/dist/index.js';

const client = new JanusClient({ baseURL: process.env.JANUS_GATEWAY_URL || 'http://localhost:8080' });

const intent = {
  type: 'request',
  id: 'test-' + Date.now(),
  method: 'transfer',
  params: { from: 'Base', to: 'Solana', amount: '0.01' },
  chain: {
    origin: 'Base',
    destination: 'Solana',
    executor: '0x0000000000000000000000000000000000000000',
    signature: '0xSIG',
    deadline: Math.floor(Date.now()/1000)+3600
  }
};

const sent = await client.sendIntent(intent);
console.log('Sent:', sent);
if (sent.ok && sent.id) {
  const fin = await client.awaitResult(sent.id, { maxWaitMs: 60_000, pollMs: 5_000 });
  console.log('Final:', fin);
}
