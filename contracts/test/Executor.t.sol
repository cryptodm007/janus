// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/Executor.sol";
import "../src/Registry.sol";

contract ExecutorTest is Test {
    Registry reg;
    Executor exe;

    bytes32 agentId = keccak256("janus:agent:0xABC");
    address owner = address(0xBEEF);
    address signer = address(0xC0FFEE);

    function setUp() public {
        reg = new Registry();
        vm.startPrank(owner);
        reg.register(agentId, signer, keccak256("constitution"));
        vm.stopPrank();

        exe = new Executor(reg);
        exe.setSpendCap(agentId, 1 ether);
    }

    function test_Submit_Succeeds() public {
        Executor.Intent memory it = Executor.Intent({
            agentId: agentId,
            intentId: keccak256("intent-1"),
            signer: signer,
            maxSpend: 0.1 ether,
            deadline: block.timestamp + 1 days,
            payload: "",
            signature: "",
            nonce: keccak256("n-1")
        });

        vm.expectEmit(true, true, false, true);
        emit Executor.IntentExecuted(agentId, it.intentId);

        exe.submit(it);
    }

    function test_Replay_Reverts() public {
        Executor.Intent memory it = Executor.Intent({
            agentId: agentId,
            intentId: keccak256("intent-2"),
            signer: signer,
            maxSpend: 0.1 ether,
            deadline: block.timestamp + 1 days,
            payload: "",
            signature: "",
            nonce: keccak256("n-2")
        });

        exe.submit(it);
        vm.expectRevert("replay");
        exe.submit(it);
    }

    function test_Expired_Reverts() public {
        Executor.Intent memory it = Executor.Intent({
            agentId: agentId,
            intentId: keccak256("intent-3"),
            signer: signer,
            maxSpend: 0.1 ether,
            deadline: block.timestamp - 1,
            payload: "",
            signature: "",
            nonce: keccak256("n-3")
        });

        vm.expectRevert("expired");
        exe.submit(it);
    }
}
