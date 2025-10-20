// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/Registry.sol";
import "../src/Executor.sol";

contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(pk);
        Registry reg = new Registry();
        Executor exe = new Executor(reg);
        vm.stopBroadcast();

        console2.log("Registry:", address(reg));
        console2.log("Executor:", address(exe));
    }
}
