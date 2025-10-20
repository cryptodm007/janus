// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/Executor.sol";
import "./helpers/SignUtils.t.sol";

contract ExecutorTest is Test, SignUtils {
    Executor exec;
    address target = address(0xBEEF);
    uint256 userPk = 0xA11CE;

    function setUp() public {
        exec = new Executor();
        exec.setWhitelist(target, true);
        exec.setCap(target, 1 ether);
    }

    function test_ExecuteValidIntent() public {
        Executor.Intent memory intent = Executor.Intent({
            target: target,
            data: abi.encodeWithSignature("doSomething()"),
            value: 0,
            deadline: block.timestamp + 1000,
            nonce: 0
        });

        (bytes memory sig, address signer) = signIntent(userPk, intent);
        exec.execute(intent, sig);
        assertEq(exec.nonces(signer), 1);
    }

    function test_RevertIf_NotWhitelisted() public {
        Executor.Intent memory intent = Executor.Intent({
            target: address(0x1234),
            data: "",
            value: 0,
            deadline: block.timestamp + 1000,
            nonce: 0
        });
        (bytes memory sig, ) = signIntent(userPk, intent);
        vm.expectRevert("target not allowed");
        exec.execute(intent, sig);
    }

    function test_RevertIf_Expired() public {
        Executor.Intent memory intent = Executor.Intent({
            target: target,
            data: "",
            value: 0,
            deadline: block.timestamp - 1,
            nonce: 0
        });
        (bytes memory sig, ) = signIntent(userPk, intent);
        vm.expectRevert("intent expired");
        exec.verifyIntent(intent, sig);
    }
}
