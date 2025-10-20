// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

interface IRegistry {
    struct Agent {
        address owner;
        address signer;
        bytes32 constitution;
        bool active;
    }

    event AgentRegistered(bytes32 indexed agentId, address owner, address signer, bytes32 constitution);
    event AgentUpdated(bytes32 indexed agentId, address signer, bytes32 constitution, bool active);

    function register(bytes32 agentId, address signer, bytes32 constitution) external;
    function update(bytes32 agentId, address signer, bytes32 constitution, bool active) external;
    function get(bytes32 agentId) external view returns (Agent memory);
    function isActive(bytes32 agentId) external view returns (bool);
    function isSigner(bytes32 agentId, address who) external view returns (bool);
}
