// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @notice Interface mínima que o DAO usará no Executor.
interface IExecutorPolicy {
    function setWhitelist(address target, bool allowed) external;
    function setCap(address target, uint256 maxValue) external;
}
