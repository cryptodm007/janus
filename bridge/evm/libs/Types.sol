// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

library Types {
    enum Finality { PENDING, FINALIZED, FAILED }

    struct CrossChainMessage {
        uint64 srcChainId;
        bytes srcAddress;
        uint64 dstChainId;
        bytes dstAddress;
        bytes32 messageId;
        uint64 nonce;
        uint64 deadline;
        bytes payload;
    }

    struct JobIntent {
        bytes32 intentHash;
        uint64 dstChainId;
        bytes dstAddress;
        uint256 escrowAmount;
        uint64 deadline;
    }
}
