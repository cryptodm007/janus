# janus/tools/print_config.py
from core.config import load_config

def _as_yaml_like(cfg) -> str:
    # impressão simples (sem deps)
    lines = []
    lines.append(f"profile:")
    lines.append(f"  name: {cfg.profile.name}")
    lines.append(f"  chain_ids:")
    for k, v in (cfg.profile.chain_ids or {}).items():
        lines.append(f"    {k}: {v}")

    lines.append(f"policy:")
    lines.append(f"  min_sig_quorum: {cfg.policy.min_sig_quorum}")
    lines.append(f"  min_ai_score: {cfg.policy.min_ai_score}")
    lines.append(f"  max_clock_skew_sec: {cfg.policy.max_clock_skew_sec}")

    lines.append(f"observability:")
    lines.append(f"  log_level: {cfg.observability.log_level}")
    lines.append(f"  metrics_enabled: {cfg.observability.metrics_enabled}")
    lines.append(f"  tracing_enabled: {cfg.observability.tracing_enabled}")

    lines.append(f"bridge:")
    lines.append(f"  vendor: {cfg.bridge.vendor}")
    lines.append(f"  poll_interval_sec: {cfg.bridge.poll_interval_sec}")
    lines.append(f"  network_timeout_sec: {cfg.bridge.network_timeout_sec}")

    return "\n".join(lines)

if __name__ == "__main__":
    cfg = load_config()
    print(_as_yaml_like(cfg))
