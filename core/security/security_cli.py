# janus/tools/security_cli.py
import argparse, json, os
from typing import Dict
from core.security.models import Principal
from core.security.policy_bindings import DEFAULT_ROLES
from core.security.acl import ACL

STORE = ".securities.json"  # armazenamento simples de principals (PoC)

def _load() -> Dict[str, dict]:
    if not os.path.exists(STORE):
        return {}
    return json.load(open(STORE, "r", encoding="utf-8"))

def _save(db: Dict[str, dict]):
    json.dump(db, open(STORE, "w", encoding="utf-8"), indent=2)

def cmd_list(args):
    print(json.dumps(_load(), indent=2))

def cmd_add(args):
    db = _load()
    p = Principal(principal_id=args.id, roles=set(args.roles or []))
    db[p.principal_id] = {"principal_id": p.principal_id, "roles": list(p.roles), "attrs": {}}
    _save(db)
    print(json.dumps(db[p.principal_id], indent=2))

def cmd_grant(args):
    db = _load()
    rec = db.get(args.id)
    if not rec:
        raise SystemExit("principal not found")
    roles = set(rec.get("roles", []))
    roles.add(args.role)
    rec["roles"] = list(roles)
    db[args.id] = rec
    _save(db)
    print(json.dumps(rec, indent=2))

def cmd_revoke(args):
    db = _load()
    rec = db.get(args.id)
    if not rec:
        raise SystemExit("principal not found")
    roles = set(rec.get("roles", []))
    roles.discard(args.role)
    rec["roles"] = list(roles)
    db[args.id] = rec
    _save(db)
    print(json.dumps(rec, indent=2))

def main():
    p = argparse.ArgumentParser(description="Janus Security CLI")
    sub = p.add_subparsers()

    s_list = sub.add_parser("list", help="lista principals")
    s_list.set_defaults(func=cmd_list)

    s_add = sub.add_parser("add", help="adiciona principal")
    s_add.add_argument("--id", required=True)
    s_add.add_argument("--roles", nargs="*", default=[])
    s_add.set_defaults(func=cmd_add)

    s_grant = sub.add_parser("grant", help="concede role a um principal")
    s_grant.add_argument("--id", required=True)
    s_grant.add_argument("--role", required=True)
    s_grant.set_defaults(func=cmd_grant)

    s_revoke = sub.add_parser("revoke", help="remove role de um principal")
    s_revoke.add_argument("--id", required=True)
    s_revoke.add_argument("--role", required=True)
    s_revoke.set_defaults(func=cmd_revoke)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
