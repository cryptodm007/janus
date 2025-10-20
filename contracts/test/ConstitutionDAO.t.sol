// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/Executor.sol";
import "../dao/ConstitutionDAO.sol";
import "../dao/IExecutorPolicy.sol";

contract ConstitutionDAOTest is Test {
    Executor executor;
    ConstitutionDAO dao;
    address proposer = address(0xB0B);

    function setUp() public {
        executor = new Executor();
        // DAO com delay curto para teste (e.g., 1 hora)
        dao = new ConstitutionDAO(3600, address(this));

        // Owner do DAO autoriza "proposer"
        dao.setProposer(proposer, true);

        // Transferir ownership do Executor para o DAO
        executor.transferOwnership(address(dao));
    }

    function test_SetWhitelist_viaDAO() public {
        // Monta a chamada ao Executor
        bytes memory data = abi.encodeWithSelector(
            IExecutorPolicy.setWhitelist.selector,
            address(0xCAFE),
            true
        );

        // Propoe (feito pelo proposer)
        vm.prank(proposer);
        bytes32 opId = dao.propose(address(executor), 0, data);

        // Avança o tempo para além do delay
        vm.warp(block.timestamp + 3601);

        // Executa (qualquer endereço pode executar após o delay)
        dao.execute(opId);

        // Valida que o alvo foi whitelisted
        assertTrue(executor.whitelist(address(0xCAFE)));
    }

    function test_SetCap_viaDAO() public {
        bytes memory data = abi.encodeWithSelector(
            IExecutorPolicy.setCap.selector,
            address(0xCAFE),
            1 ether
        );

        vm.prank(proposer);
        bytes32 opId = dao.propose(address(executor), 0, data);
        vm.warp(block.timestamp + 3601);
        dao.execute(opId);

        assertEq(executor.caps(address(0xCAFE)), 1 ether);
    }

    function test_RevertTooEarly() public {
        bytes memory data = abi.encodeWithSelector(
            IExecutorPolicy.setWhitelist.selector,
            address(0xCAFE),
            true
        );
        vm.prank(proposer);
        bytes32 opId = dao.propose(address(executor), 0, data);
        vm.expectRevert("too early");
        dao.execute(opId);
    }
}
