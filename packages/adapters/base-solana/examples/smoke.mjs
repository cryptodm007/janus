import { sendMessage, awaitProveAndFinalize } from '../dist/index.js';

const env = {
  type: 'request',
  id: 'intent-demo-' + Date.now(),
  method: 'call_tool',
  params: { name: 'swap', arguments: { tokenIn: 'USDC', tokenOut: 'SOL', amount: '100' } },
  chain: { origin: 'Base', destination: 'Solana', executor: '0xExecutor', signature: '0xSig' }
};

const payload = Buffer.from(JSON.stringify(env), 'utf8');
const s = await sendMessage({ direction: 'BASE_TO_SOLANA', payload, intentId: env.id });
console.log('sendMessage:', s);

const f = await awaitProveAndFinalize(env.id, { maxWaitMs: 30_000, pollMs: 3_000 });
console.log('awaitProveAndFinalize:', f);
