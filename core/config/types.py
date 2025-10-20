# janus/core/config/types.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class PolicyConfig:
    min_sig_quorum: float = 0.67
    min_ai_score: float = 0.65
    max_clock_skew_sec: int = 45

@dataclass
class ObservabilityConfig:
    log_level: str = "INFO"            # DEBUG/INFO/WARN/ERROR
    metrics_enabled: bool = True
    tracing_enabled: bool = True

@dataclass
class BridgeConfig:
    poll_interval_sec: int = 10
    vendor: str = "base_solana"        # nome lógico do bridge vendor ativo
    network_timeout_sec: int = 10

@dataclass
class NetworkProfile:
    name: str = "dev"                  # dev | testnet | mainnet
    chain_ids: Dict[str, str] = None   # ex.: {"base":"base-sepolia", "solana":"devnet"}

@dataclass
class JanusConfig:
    profile: NetworkProfile = NetworkProfile()
    policy: PolicyConfig = PolicyConfig()
    observability: ObservabilityConfig = ObservabilityConfig()
    bridge: BridgeConfig = BridgeConfig()
    extras: Dict[str, Any] = None      # espaço para futuros campos não tipados
