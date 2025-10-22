// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 { function transferFrom(address, address, uint256) external returns (bool);
                   function transfer(address, uint256) external returns (bool); }

contract AgentStaking {
    IERC20 public immutable JNS;
    mapping(address => uint256) public stake;

    event Staked(address indexed agent, uint256 amount);
    event Unstaked(address indexed agent, uint256 amount);
    event Slashed(address indexed agent, uint256 amount);

    constructor(address jns) { JNS = IERC20(jns); }

    function stakeUp(uint256 amount) external {
        require(amount > 0, "amount");
        JNS.transferFrom(msg.sender, address(this), amount);
        stake[msg.sender] += amount;
        emit Staked(msg.sender, amount);
    }

    function unstake(uint256 amount) external {
        require(stake[msg.sender] >= amount, "insufficient");
        stake[msg.sender] -= amount;
        JNS.transfer(msg.sender, amount);
        emit Unstaked(msg.sender, amount);
    }

    function slash(address agent, uint256 amount) external {
        // TODO: access control (governance/guardian)
        require(stake[agent] >= amount, "insufficient");
        stake[agent] -= amount;
        // queima ou tesouraria
        emit Slashed(agent, amount);
    }
}
