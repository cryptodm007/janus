// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

// Tarefa: hash do input/output; pagamento ao agente; verificação simples
interface IRewards { function reward(address agent, uint256 amount) external; }

contract TaskSettlement {
    IRewards public rewards;
    address public verifier; // contrato/EOA que atesta conclusão

    event TaskClosed(bytes32 taskId, address agent, uint256 amount);

    constructor(address _rewards, address _verifier) {
        rewards = IRewards(_rewards);
        verifier = _verifier;
    }

    function closeTask(bytes32 taskId, address agent, uint256 amount) external {
        require(msg.sender == verifier, "only verifier");
        rewards.reward(agent, amount);
        emit TaskClosed(taskId, agent, amount);
    }
}
