# janus/core/config/loader.py
import json, os
from typing import Dict, Any
from .types import JanusConfig, NetworkProfile, PolicyConfig, ObservabilityConfig, BridgeConfig

# --- helpers de merge ---
def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a or {})
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _parse_bool(s: str) -> bool:
    return s.strip().lower() in ("1","true","yes","y","on")

# --- profiles padrão (paths relativos) ---
def _profiles_dir() -> str:
    here = os.path.dirname(__file__)
    return os.path.join(here, "profiles")

def load_profile(profile_name: str) -> Dict[str, Any]:
    profiles = {
        "dev":      os.path.join(_profiles_dir(), "dev.json"),
        "testnet":  os.path.join(_profiles_dir(), "testnet.json"),
        "mainnet":  os.path.join(_profiles_dir(), "mainnet.json"),
    }
    path = profiles.get(profile_name.lower())
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Profile '{profile_name}' not found.")
    return _read_json(path)

# --- overrides via ambiente ---
def env_overrides() -> Dict[str, Any]:
    # mapeamento plano -> config nested
    env = os.environ
    o: Dict[str, Any] = {}

    # profile
    prof = env.get("JANUS_PROFILE")
    if prof:
        o["profile"] = o.get("profile", {})
        o["profile"]["name"] = prof

    # observability
    lvl = env.get("JANUS_LOG_LEVEL")
    if lvl:
        o["observability"] = o.get("observability", {})
        o["observability"]["log_level"] = lvl

    if "JANUS_METRICS_ENABLED" in env:
        o.setdefault("observability", {})["metrics_enabled"] = _parse_bool(env["JANUS_METRICS_ENABLED"])
    if "JANUS_TRACING_ENABLED" in env:
        o.setdefault("observability", {})["tracing_enabled"] = _parse_bool(env["JANUS_TRACING_ENABLED"])

    # policy
    if "JANUS_POLICY_MIN_SIG_QUORUM" in env:
        o.setdefault("policy", {})["min_sig_quorum"] = float(env["JANUS_POLICY_MIN_SIG_QUORUM"])
    if "JANUS_POLICY_MIN_AI_SCORE" in env:
        o.setdefault("policy", {})["min_ai_score"] = float(env["JANUS_POLICY_MIN_AI_SCORE"])
    if "JANUS_POLICY_MAX_CLOCK_SKEW_SEC" in env:
        o.setdefault("policy", {})["max_clock_skew_sec"] = int(env["JANUS_POLICY_MAX_CLOCK_SKEW_SEC"])

    # bridge
    if "JANUS_BRIDGE_POLL_INTERVAL_SEC" in env:
        o.setdefault("bridge", {})["poll_interval_sec"] = int(env["JANUS_BRIDGE_POLL_INTERVAL_SEC"])
    if "JANUS_BRIDGE_VENDOR" in env:
        o.setdefault("bridge", {})["vendor"] = env["JANUS_BRIDGE_VENDOR"]
    if "JANUS_BRIDGE_TIMEOUT_SEC" in env:
        o.setdefault("bridge", {})["network_timeout_sec"] = int(env["JANUS_BRIDGE_TIMEOUT_SEC"])

    # chain ids (ex.: JANUS_CHAIN_BASE=base-sepolia)
    for key, val in env.items():
        if key.startswith("JANUS_CHAIN_"):
            chain = key.replace("JANUS_CHAIN_", "").lower()
            o.setdefault("profile", {})["chain_ids"] = o.get("profile", {}).get("chain_ids", {})
            o["profile"]["chain_ids"][chain] = val

    return o

# --- carregador principal ---
def load_config() -> JanusConfig:
    default_profile = os.getenv("JANUS_PROFILE", "dev").lower()
    base = load_profile(default_profile)

    # Overrides por arquivo específico (opcional) - JANUS_CONFIG_FILE=/path/config.json
    cfg_file = os.getenv("JANUS_CONFIG_FILE")
    if cfg_file and os.path.exists(cfg_file):
        base = _deep_merge(base, _read_json(cfg_file))

    # Overrides por ENV
    base = _deep_merge(base, env_overrides())

    # Materializa em dataclasses
    prof = base.get("profile", {})
    policy = base.get("policy", {})
    obs = base.get("observability", {})
    br = base.get("bridge", {})
    extras = base.get("extras", {})

    cfg = JanusConfig(
        profile=NetworkProfile(
            name=prof.get("name", "dev"),
            chain_ids=prof.get("chain_ids", {}) or {},
        ),
        policy=PolicyConfig(
            min_sig_quorum=float(policy.get("min_sig_quorum", 0.67)),
            min_ai_score=float(policy.get("min_ai_score", 0.65)),
            max_clock_skew_sec=int(policy.get("max_clock_skew_sec", 45)),
        ),
        observability=ObservabilityConfig(
            log_level=str(obs.get("log_level", "INFO")).upper(),
            metrics_enabled=bool(obs.get("metrics_enabled", True)),
            tracing_enabled=bool(obs.get("tracing_enabled", True)),
        ),
        bridge=BridgeConfig(
            poll_interval_sec=int(br.get("poll_interval_sec", 10)),
            vendor=str(br.get("vendor", "base_solana")),
            network_timeout_sec=int(br.get("network_timeout_sec", 10)),
        ),
        extras=extras or {},
    )

    return cfg
