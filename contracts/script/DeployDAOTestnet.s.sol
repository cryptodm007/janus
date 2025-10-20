// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/Executor.sol";
import "../src/Registry.sol";
import "../dao/ConstitutionDAO.sol";

contract DeployDAOTestnet is Script {
    function run() external {
        uint256 deployerPk = vm.envUint("PRIVATE_KEY");
        string memory rpc = vm.envString("RPC_URL_BASE_SEPOLIA"); // Testnet

        vm.createSelectFork(rpc);
        vm.startBroadcast(deployerPk);

        // Se já tiver Executor/Registry em testnet, carregue pelos endereços em vez de deployar de novo.
        Executor executor = new Executor();
        Registry registry = new Registry(address(executor));

        // DAO com delay de 1h (ajuste conforme necessário)
        ConstitutionDAO dao = new ConstitutionDAO(3600, msg.sender);

        // Transferir ownership do Executor para o DAO
        executor.transferOwnership(address(dao));

        console2.log("Executor (testnet):", address(executor));
        console2.log("Registry (testnet):", address(registry));
        console2.log("ConstitutionDAO (testnet):", address(dao));

        vm.stopBroadcast();
    }
}
