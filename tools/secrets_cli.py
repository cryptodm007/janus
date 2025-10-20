# janus/tools/secrets_cli.py
import argparse, json, base64
from core.secrets.keystore import LocalKeyStore
from core.secrets.rotation import RotationPolicy, rotate_if_needed

def cmd_list(args):
    ks = LocalKeyStore()
    items = ks.list_keys(only_active=args.active)
    print(json.dumps([vars(i) for i in items], indent=2))

def cmd_generate(args):
    ks = LocalKeyStore()
    rec = ks.generate_hmac_key(key_id=args.key_id, bytes_len=args.bytes, ttl_days=args.ttl_days)
    print(json.dumps(vars(rec), indent=2))

def cmd_deactivate(args):
    ks = LocalKeyStore()
    ks.deactivate(args.key_id)
    print(f"deactivated: {args.key_id}")

def cmd_rotate(args):
    ks = LocalKeyStore()
    new_rec = rotate_if_needed(ks, policy=RotationPolicy(max_age_days=args.max_age_days, max_active=args.max_active))
    if new_rec:
        print(json.dumps(vars(new_rec), indent=2))
    else:
        print("no-rotation")

def main():
    p = argparse.ArgumentParser(description="Janus Secrets CLI")
    sub = p.add_subparsers()

    p_list = sub.add_parser("list", help="lista chaves")
    p_list.add_argument("--active", action="store_true", help="apenas ativas")
    p_list.set_defaults(func=cmd_list)

    p_gen = sub.add_parser("generate", help="gera chave HMAC")
    p_gen.add_argument("--key-id", default=None)
    p_gen.add_argument("--bytes", type=int, default=32)
    p_gen.add_argument("--ttl-days", type=int, default=90)
    p_gen.set_defaults(func=cmd_generate)

    p_deac = sub.add_parser("deactivate", help="desativa chave")
    p_deac.add_argument("key_id")
    p_deac.set_defaults(func=cmd_deactivate)

    p_rot = sub.add_parser("rotate", help="aplica política de rotação")
    p_rot.add_argument("--max-age-days", type=int, default=90)
    p_rot.add_argument("--max-active", type=int, default=2)
    p_rot.set_defaults(func=cmd_rotate)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
