// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import {IRegistry} from "./interfaces/IRegistry.sol";

contract Registry is IRegistry {
    mapping(bytes32 => Agent) private agents;

    modifier onlyOwner(bytes32 agentId) {
        require(agents[agentId].owner == msg.sender, "not owner");
        _;
    }

    function register(bytes32 agentId, address signer, bytes32 constitution) external {
        require(agents[agentId].owner == address(0), "exists");
        require(signer != address(0), "bad signer");
        agents[agentId] = Agent({
            owner: msg.sender,
            signer: signer,
            constitution: constitution,
            active: true
        });
        emit AgentRegistered(agentId, msg.sender, signer, constitution);
    }

    function update(bytes32 agentId, address signer, bytes32 constitution, bool active) external onlyOwner(agentId) {
        require(signer != address(0), "bad signer");
        Agent storage a = agents[agentId];
        a.signer = signer;
        a.constitution = constitution;
        a.active = active;
        emit AgentUpdated(agentId, signer, constitution, active);
    }

    function get(bytes32 agentId) external view returns (Agent memory) {
        return agents[agentId];
    }

    function isActive(bytes32 agentId) external view returns (bool) {
        return agents[agentId].active;
    }

    function isSigner(bytes32 agentId, address who) external view returns (bool) {
        return agents[agentId].signer == who;
    }
}
