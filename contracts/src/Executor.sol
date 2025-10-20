// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import {IRegistry} from "./interfaces/IRegistry.sol";

contract Executor {
    IRegistry public immutable registry;

    mapping(bytes32 => bool) public usedNonces;
    mapping(bytes32 => uint256) public spendCapByAgent;

    event IntentReceived(bytes32 indexed agentId, bytes32 indexed intentId, address indexed caller);
    event IntentExecuted(bytes32 indexed agentId, bytes32 indexed intentId);
    event IntentRejected(bytes32 indexed agentId, bytes32 indexed intentId, string reason);

    struct Intent {
        bytes32 agentId;
        bytes32 intentId;
        address signer;
        uint256 maxSpend;
        uint256 deadline;
        bytes payload;
        bytes signature;
        bytes32 nonce;
    }

    constructor(IRegistry _registry) {
        registry = _registry;
    }

    function setSpendCap(bytes32 agentId, uint256 cap) external {
        spendCapByAgent[agentId] = cap;
    }

    function submit(Intent calldata i) external {
        emit IntentReceived(i.agentId, i.intentId, msg.sender);

        if (!registry.isActive(i.agentId)) {
            emit IntentRejected(i.agentId, i.intentId, "agent inactive");
            revert("agent inactive");
        }
        if (usedNonces[i.nonce]) {
            emit IntentRejected(i.agentId, i.intentId, "replay");
            revert("replay");
        }
        if (i.deadline < block.timestamp) {
            emit IntentRejected(i.agentId, i.intentId, "expired");
            revert("expired");
        }
        if (i.maxSpend > spendCapByAgent[i.agentId]) {
            emit IntentRejected(i.agentId, i.intentId, "cap exceeded");
            revert("cap exceeded");
        }

        require(registry.isSigner(i.agentId, i.signer), "invalid signer");

        usedNonces[i.nonce] = true;

        // TODO: decodificar payload e chamar contratos whitelisted
        emit IntentExecuted(i.agentId, i.intentId);
    }
}
