// Exporte contadores simples; plugar depois no seu Prometheus/OTel
let aiTasks = 0;
let aiTasksSuccess = 0;
let aiTasksFail = 0;

export function incTask() { aiTasks++; }
export function incTaskSuccess() { aiTasksSuccess++; }
export function incTaskFail() { aiTasksFail++; }

export function snapshot() {
  return { ai_tasks_total: aiTasks, ai_tasks_success_total: aiTasksSuccess, ai_tasks_fail_total: aiTasksFail };
}
