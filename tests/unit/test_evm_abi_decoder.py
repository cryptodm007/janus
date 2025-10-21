# tests/unit/test_evm_abi_decoder.py
import json
import pytest
from bridge.decoders.evm_abi import EVMAbiDecoder
from web3 import Web3

@pytest.fixture
def simple_abi(tmp_path):
    abi = [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "from", "type": "address"},
                {"indexed": True, "name": "to",   "type": "address"},
                {"indexed": False,"name": "value","type": "uint256"}
            ],
            "name": "Transfer",
            "type": "event"
        }
    ]
    path = tmp_path / "SimpleToken.json"
    path.write_text(json.dumps(abi))
    return str(path)

def test_decoder_recognizes_event(simple_abi):
    decoder = EVMAbiDecoder(abi_files=[simple_abi])
    # Construct a log for Transfer event: from=0x..1, to=0x..2, value=123
    topic0 = Web3.keccak(text="Transfer(address,address,uint256)").hex()
    log = {
        "address": "0x0000000000000000000000000000000000000000",
        "topics": [topic0,
                   Web3.to_bytes(hexstr="0x0000000000000000000000000000000000000001"),
                   Web3.to_bytes(hexstr="0x0000000000000000000000000000000000000002")],
        "data": Web3.to_hex(Web3.to_bytes(123))
    }
    decoded = decoder.decode(log)
    assert decoded is not None
    assert decoded["event_name"] == "Transfer"
    assert decoded["args"]["from"] == "0x0000000000000000000000000000000000000001"
    assert decoded["args"]["to"]   == "0x0000000000000000000000000000000000000002"
    assert int(decoded["args"]["value"]) == 123
