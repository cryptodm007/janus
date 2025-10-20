// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./interfaces/IRegistry.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Executor is Ownable {
    using ECDSA for bytes32;

    event IntentQueued(bytes32 indexed intentHash, address indexed signer, uint256 deadline);
    event IntentExecuted(bytes32 indexed intentHash, address indexed executor, bool success);
    event WhitelistUpdated(address target, bool allowed);
    event CapUpdated(address target, uint256 maxValue);

    struct Intent {
        address target;
        bytes data;
        uint256 value;
        uint256 deadline;
        uint256 nonce;
    }

    mapping(address => uint256) public nonces;
    mapping(address => bool) public whitelist;
    mapping(address => uint256) public caps; // máximo de value permitido por target

    bytes32 public constant INTENT_TYPEHASH = keccak256(
        "Intent(address target,bytes data,uint256 value,uint256 deadline,uint256 nonce)"
    );
    bytes32 private immutable DOMAIN_SEPARATOR;

    constructor() {
        uint256 chainId;
        assembly {
            chainId := chainid()
        }
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256(bytes("JanusExecutor")),
                keccak256(bytes("1")),
                chainId,
                address(this)
            )
        );
    }

    modi
