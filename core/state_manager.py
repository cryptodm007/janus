# janus/core/state_manager.py
class StateManager:
    """
    Gerencia o estado sincronizado entre múltiplas redes.
    """
    def __init__(self):
        self._state = {}
        self._last_update = None

    def update_state(self, new_state: dict):
        self._state = new_state
        self._last_update = new_state.get("timestamp")

    def get_state(self) -> dict:
        return self._state

    def get_last_update(self):
        return self._last_update
