type Level = 'debug' | 'info' | 'warn' | 'error';
const level: Level = (process.env.LOG_LEVEL as Level) || 'info';

function log(l: Level, msg: string, extra?: Record<string, unknown>) {
  const payload = { level: l, msg, ts: new Date().toISOString(), ...extra };
  // simples: imprime JSON por linha
  console.log(JSON.stringify(payload));
}

export const logger = {
  debug: (msg: string, extra?: Record<string, unknown>) => level === 'debug' && log('debug', msg, extra),
  info: (msg: string, extra?: Record<string, unknown>) => log('info', msg, extra),
  warn: (msg: string, extra?: Record<string, unknown>) => log('warn', msg, extra),
  error: (msg: string, extra?: Record<string, unknown>) => log('error', msg, extra),
};
