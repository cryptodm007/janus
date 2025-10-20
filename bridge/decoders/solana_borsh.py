# bridge/decoders/solana_borsh.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from borsh_construct import U8, U64
from construct import Bytes

TYPE_MAP = {
    "u8": U8,
    "u64": U64,
}

class SolanaBorshDecoder:
    """
    Decodificador declarativo: recebe um dict de layout por program_id (config).
    O primeiro campo (discriminator) define a variante (event_tag).
    """
    def __init__(self, layouts: Dict[str, Any]):
        self.layouts = layouts or {}

    def decode(self, program_id: str, raw_bytes: bytes) -> Optional[Dict[str, Any]]:
        layout = self.layouts.get(program_id)
        if not layout:
            return None

        disc_type = layout.get("discriminator", "u8")
        disc_parser = TYPE_MAP.get(disc_type)
        if not disc_parser:
            return None

        i = 0
        event_tag = disc_parser.parse(raw_bytes[i:i+disc_parser.sizeof()])
        i += disc_parser.sizeof()

        variants = layout.get("variants", {})
        variant = variants.get(str(event_tag))
        if not variant:
            return {"event_tag": event_tag, "raw": raw_bytes.hex()}

        out = {"event_tag": event_tag, "name": variant.get("name")}
        for field in (variant.get("fields") or []):
            ftype = field["type"]
            fname = field["name"]
            if ftype == "u8" or ftype == "u64":
                parser = TYPE_MAP[ftype]
                value = parser.parse(raw_bytes[i:i+parser.sizeof()])
                i += parser.sizeof()
                out[fname] = int(value)
            elif ftype == "bytes_len":
                # bytes com tamanho indicado por outro campo já lido (ref)
                ref = field["ref"]
                blen = int(out[ref])
                value = Bytes(blen).parse(raw_bytes[i:i+blen])
                i += blen
                # decodifica como UTF-8 se possível; senão hex
                try:
                    out[fname] = value.decode("utf-8")
                except Exception:
                    out[fname] = value.hex()
            else:
                # tipo não suportado — retorna o restante bruto
                out[fname] = raw_bytes[i:].hex()
                break
        return out
