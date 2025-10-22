/**
 * Canal de eventos AI → Bridge.
 * Permite que agentes recebam notificações on-chain em tempo real.
 */
import EventEmitter from "events";
export const aiChannel = new EventEmitter();

// Exemplo: publicar evento quando nova liquidez detectada
export function emitLiquidityEvent(pair: string, delta: number) {
  aiChannel.emit("POOL_IMBALANCE_DETECTED", { pair, delta });
}
