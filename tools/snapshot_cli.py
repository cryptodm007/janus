# janus/tools/snapshot_cli.py
import argparse, json, os
from core.persistence.store import SnapshotStore
from core.persistence.manifest import SnapshotManifest
from core.state_manager import StateManager

def cmd_list(args):
    man = SnapshotManifest()
    print(json.dumps(man.list(), indent=2, ensure_ascii=False))

def cmd_latest(args):
    man = SnapshotManifest()
    print(json.dumps(man.latest() or {}, indent=2, ensure_ascii=False))

def cmd_create(args):
    st = StateManager()  # em produção, você passará o mesmo StateManager do app
    store = SnapshotStore()
    meta = store.save(st.get_state() if hasattr(st, "get_state") else {})
    SnapshotManifest(store.root).add(meta)
    print(json.dumps(meta.__dict__, indent=2, ensure_ascii=False))

def cmd_restore(args):
    store = SnapshotStore()
    state = StateManager()
    data = store.load(args.file)
    # sobrescreve o estado (stub simples)
    if hasattr(state, "update_state"):
        state.update_state(data)
    print(json.dumps({"restored_from": args.file, "timestamp": data.get("timestamp")}, indent=2, ensure_ascii=False))

def cmd_prune(args):
    man = SnapshotManifest()
    store = SnapshotStore()
    to_delete = man.prune(keep_last=args.keep_last, keep_days=args.keep_days)
    for f in to_delete:
        store.delete(f)
    print(json.dumps({"deleted": to_delete}, indent=2, ensure_ascii=False))

def main():
    p = argparse.ArgumentParser(description="Janus Snapshot CLI")
    sub = p.add_subparsers()

    s_list = sub.add_parser("list", help="lista snapshots")
    s_list.set_defaults(func=cmd_list)

    s_latest = sub.add_parser("latest", help="mostra último snapshot")
    s_latest.set_defaults(func=cmd_latest)

    s_create = sub.add_parser("create", help="cria snapshot agora")
    s_create.set_defaults(func=cmd_create)

    s_restore = sub.add_parser("restore", help="restaura de um arquivo")
    s_restore.add_argument("file", help="nome do arquivo em snapshots/")
    s_restore.set_defaults(func=cmd_restore)

    s_prune = sub.add_parser("prune", help="aplica retenção (mantém últimos N e janela D dias)")
    s_prune.add_argument("--keep-last", type=int, default=10)
    s_prune.add_argument("--keep-days", type=int, default=7)
    s_prune.set_defaults(func=cmd_prune)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
