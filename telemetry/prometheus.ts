// contador simples; em produção use prom-client/otel
let counters: Record<string, number> = {
  ai_tasks_total: 0,
  ai_tasks_success_total: 0,
  ai_tasks_fail_total: 0,
  onchain_settlement_total: 0
};

export function inc(name: keyof typeof counters, v: number = 1) {
  counters[name] = (counters[name] || 0) + v;
}

export function metricsText() {
  return Object.entries(counters)
    .map(([k,v]) => `# TYPE ${k} counter\n${k} ${v}`)
    .join("\n") + "\n";
}
