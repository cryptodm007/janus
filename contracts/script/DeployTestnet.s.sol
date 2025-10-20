// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "forge-std/Script.sol";
import "../src/Executor.sol";
import "../src/Registry.sol";

contract DeployTestnet is Script {
    function run() external {
        uint256 deployerPk = vm.envUint("PRIVATE_KEY");
        string memory rpc = vm.envString("RPC_URL_BASE_SEPOLIA"); // Testnet

        vm.createSelectFork(rpc);
        vm.startBroadcast(deployerPk);

        Executor executor = new Executor();
        Registry registry = new Registry(address(executor));

        executor.transferOwnership(msg.sender);
        registry.transferOwnership(msg.sender);

        console2.log("Executor (testnet):", address(executor));
        console2.log("Registry (testnet):", address(registry));
        vm.stopBroadcast();
    }
}
