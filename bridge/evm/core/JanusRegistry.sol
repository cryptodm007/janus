// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { IBridgeAdapter } from "../interfaces/IBridgeAdapter.sol";
import { Types } from "../libs/Types.sol";

/// @title JanusRegistry – Registro de Jobs, Escrow e Liquidação
/// @notice Mantém intents, bloqueia valores e liquida com base em acks vindos via ponte.
contract JanusRegistry {
    IBridgeAdapter public bridge;
    address public admin;

    struct Job {
        address creator;
        bytes32 intentHash;
        uint64 dstChainId;
        bytes dstAddress;
        uint256 escrowAmount;
        uint64 deadline;
        bool settled;
    }

    mapping(bytes32 => Job) public jobs;

    event JobInitiated(bytes32 indexed jobId, address indexed creator, uint64 dstChainId, uint64 deadline, uint256 escrowAmount);
    event JobSettled(bytes32 indexed jobId, bool success);

    constructor(address bridgeAdapter) {
        bridge = IBridgeAdapter(bridgeAdapter);
        admin = msg.sender;
    }

    function setBridge(address bridgeAdapter) external {
        require(msg.sender == admin, "only admin");
        bridge = IBridgeAdapter(bridgeAdapter);
    }

    function initiateJob(
        bytes32 intentHash,
        uint64 dstChainId,
        bytes calldata dstAddress,
        bytes calldata payload,
        uint64 deadline
    ) external payable returns (bytes32 jobId) {
        require(deadline > block.timestamp, "deadline in past");
        require(msg.value > 0, "escrow required");

        jobId = keccak256(abi.encodePacked(intentHash, msg.sender, dstChainId, block.number));

        jobs[jobId] = Job({
            creator: msg.sender,
            intentHash: intentHash,
            dstChainId: dstChainId,
            dstAddress: dstAddress,
            escrowAmount: msg.value,
            deadline: deadline,
            settled: false
        });

        bridge.sendMessage(dstChainId, dstAddress, payload, 0);
        emit JobInitiated(jobId, msg.sender, dstChainId, deadline, msg.value);
    }

    function onMessageReceived(bytes32 jobId, bool success, bytes calldata proof) external {
        require(msg.sender == address(bridge), "only bridge");
        require(!jobs[jobId].settled, "already settled");
        require(jobs[jobId].deadline >= block.timestamp, "expired");
        require(bridge.verifyMessage(jobId, proof), "invalid proof");

        jobs[jobId].settled = true;

        (bool ok, ) = jobs[jobId].creator.call{value: jobs[jobId].escrowAmount}("");
        require(ok, "escrow transfer failed");

        emit JobSettled(jobId, success);
    }
}
