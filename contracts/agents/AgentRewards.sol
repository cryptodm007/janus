// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 { function transfer(address, uint256) external returns (bool); }

contract AgentRewards {
    IERC20 public immutable JNS;
    address public controller;

    event Rewarded(address indexed agent, uint256 amount);

    constructor(address jns, address _controller) {
        JNS = IERC20(jns);
        controller = _controller;
    }

    function reward(address agent, uint256 amount) external {
        require(msg.sender == controller, "only controller");
        require(JNS.transfer(agent, amount), "transfer fail");
        emit Rewarded(agent, amount);
    }
}
