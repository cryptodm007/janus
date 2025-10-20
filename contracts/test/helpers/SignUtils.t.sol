// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../../src/Executor.sol";

contract SignUtils is Test {
    Executor executor;

    function setUp() public {
        executor = new Executor();
    }

    function signIntent(
        uint256 pk,
        Executor.Intent memory intent
    ) public view returns (bytes memory sig, address signer) {
        bytes32 structHash = keccak256(
            abi.encode(
                executor.INTENT_TYPEHASH(),
                intent.target,
                keccak256(intent.data),
                intent.value,
                intent.deadline,
                intent.nonce
            )
        );
        bytes32 digest = keccak256(
            abi.encodePacked("\x19\x01", executor.DOMAIN_SEPARATOR(), structHash)
        );
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, digest);
        sig = abi.encodePacked(r, s, v);
        signer = vm.addr(pk);
    }
}
