# janus/bridge/sync/sync_manager.py
import asyncio
from bridge.vendor.bridge_base_solana import BaseSolanaBridge
from core.state_manager import StateManager

class SyncManager:
    def __init__(self, bridge: BaseSolanaBridge, state_manager: StateManager):
        self.bridge = bridge
        self.state_manager = state_manager

    async def sync_loop(self, interval_sec: int = 10):
        while True:
            try:
                base_state = await self.bridge.get_base_state()
                solana_state = await self.bridge.get_solana_state()
                merged_state = self.merge_states(base_state, solana_state)
                self.state_manager.update_state(merged_state)
                await asyncio.sleep(interval_sec)
            except Exception as e:
                print(f"[SYNC ERROR] {e}")
                await asyncio.sleep(5)

    def merge_states(self, base_state, solana_state):
        # Estratégia simples: escolhe o estado com timestamp mais recente.
        if base_state["timestamp"] > solana_state["timestamp"]:
            return base_state
        return solana_state
