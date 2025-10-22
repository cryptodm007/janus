import { snapshot as ai } from "./ai/metrics.js";

export function collectAll() {
  return {
    ai,
    uptime_s: process.uptime(),
    timestamp: new Date().toISOString()
  };
}
