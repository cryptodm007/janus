/**
 * Bridge Adapter → AI Notifier
 * Publica eventos do lado Solana para o AI Hub via HTTP ou WebSocket.
 */
import axios from "axios";

export async function notifyAI(event: string, payload: any) {
  try {
    await axios.post(process.env.AI_HUB_URL || "http://localhost:7331", {
      tool: "janus.event.notify",
      input: { event, payload }
    });
    console.log(`[Bridge→AI] Evento ${event} enviado.`);
  } catch (e) {
    console.error("Falha ao notificar AI Hub:", e);
  }
}
