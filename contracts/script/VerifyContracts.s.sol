// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";

contract VerifyContracts is Script {
    function run() external {
        string memory executor = vm.envString("EXECUTOR_ADDR");
        string memory registry = vm.envString("REGISTRY_ADDR");
        string memory etherscanKey = vm.envString("ETHERSCAN_API_KEY");
        string memory rpc = vm.envString("RPC_URL_BASE_MAINNET");

        string ;
        inputs[0] = "forge";
        inputs[1] = "verify-contract";
        inputs[2] = executor;
        inputs[3] = "contracts/src/Executor.sol:Executor";
        inputs[4] = "--etherscan-api-key";
        inputs[5] = etherscanKey;
        vm.ffi(inputs);

        string ;
        inputs2[0] = "forge";
        inputs2[1] = "verify-contract";
        inputs2[2] = registry;
        inputs2[3] = "contracts/src/Registry.sol:Registry";
        inputs2[4] = "--etherscan-api-key";
        inputs2[5] = etherscanKey;
        vm.ffi(inputs2);

        console2.log("Verification submitted to BaseScan");
    }
}
