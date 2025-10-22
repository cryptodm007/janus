/**
 * AI Action Manager
 * Responsável por receber requisições de IA (MCP/API)
 * e rotear para nodes ou serviços Janus.
 */

import { queueTask } from "../services/queue/index.js";

export async function handleAIAction(node: string, params: Record<string, any>) {
  const taskId = `ai_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
  await queueTask({ id: taskId, node, params, origin: "ai" });
  return { taskId, status: "queued" };
}
