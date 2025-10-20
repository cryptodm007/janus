import morgan from 'morgan';
import client from 'prom-client';
import express from 'express';
import * as dotenv from 'dotenv';
import { logger } from './logger';
import { validateEnvelope } from './validator';
import { sendMessage, awaitProveAndFinalize } from '@janus/adapter-base-solana';

dotenv.config({ path: new URL('../.env', import.meta.url).pathname });

const app = express();
app.use(express.json({ limit: '512kb' }));

const PORT = Number(process.env.PORT || 8080);
const MAX_WAIT_MS = Number(process.env.ADAPTER_MAX_WAIT_MS || 15 * 60_000);
const POLL_MS = Number(process.env.ADAPTER_POLL_MS || 5_000);

app.get('/healthz', (_req, res) => res.status(200).json({ ok: true }));
app.get('/metrics', (_req, res) => res.status(200).send('# TODO: metrics'));

app.post('/mcp/intent', async (req, res) => {
  const v = validateEnvelope(req.body);
  if (!v.ok) {
    logger.warn('invalid envelope', { error: v.error });
    return res.status(400).json({ ok: false, error: v.error });
  }
  const env = v.data;
  logger.info('intent received', { id: env.id, method: env.method, origin: env.chain.origin, destination: env.chain.destination });

  try {
    const direction = env.chain.origin === 'Base' ? 'BASE_TO_SOLANA' : 'SOLANA_TO_BASE';
    const payload = Buffer.from(JSON.stringify(env), 'utf-8'); // simples: serializa envelope

    const send = await sendMessage({ direction, payload, intentId: env.id });
    logger.info('message queued', { id: env.id, status: send.status });

    // Se Base→Solana, precisamos aguardar etapas de prove/finalize (stub)
    if (direction === 'BASE_TO_SOLANA') {
      const fin = await awaitProveAndFinalize(env.id, { maxWaitMs: MAX_WAIT_MS, pollMs: POLL_MS });
      logger.info('finalize result', { id: env.id, status: fin.status });

      if (fin.status in { FINALIZED: true, EXECUTED: true }) {
        return res.status(202).json({ ok: true, id: env.id, status: fin.status });
      }
      return res.status(504).json({ ok: false, id: env.id, status: fin.status, error: fin.error || 'timeout' });
    }

    // Se Solana→Base (outras direções): responder queued por enquanto
    return res.status(202).json({ ok: true, id: env.id, status: send.status });
  } catch (e: any) {
    logger.error('intent error', { id: env.id, err: String(e?.message || e) });
    return res.status(500).json({ ok: false, error: 'internal_error' });
  }
});

app.listen(PORT, () => {
  logger.info('gateway listening', { port: PORT, env: process.env.NODE_ENV || 'development' });
});
