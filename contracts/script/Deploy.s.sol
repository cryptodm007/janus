// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/Executor.sol";
import "../src/Registry.sol";

contract Deploy is Script {
    function run() external {
        vm.startBroadcast();
        Executor executor = new Executor();
        Registry registry = new Registry(address(executor));
        executor.transferOwnership(msg.sender);
        registry.transferOwnership(msg.sender);
        vm.stopBroadcast();
    }
}
