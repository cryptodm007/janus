// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IExecutorPolicy} from "./IExecutorPolicy.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ConstitutionDAO (mínimo viável com timelock)
 * - Mantém uma lista de proponentes (council).
 * - Cada operação proposta fica em fila até "eta" (delay).
 * - Após "eta", qualquer um pode executar.
 * - O DAO deve ser o "owner" do Executor para aplicar políticas.
 */
contract ConstitutionDAO is Ownable {
    event ProposerSet(address indexed proposer, bool allowed);
    event DelayUpdated(uint256 newDelay);
    event Proposed(bytes32 indexed opId, address indexed target, uint256 value, bytes data, uint256 eta);
    event Executed(bytes32 indexed opId, bool success);
    event Cancelled(bytes32 indexed opId);

    struct Operation {
        address target;
        uint256 value;
        bytes data;
        uint256 eta;
        bool executed;
        bool exists;
    }

    mapping(address => bool) public isProposer;
    uint256 public delay; // segundos
    mapping(bytes32 => Operation) public ops;

    constructor(uint256 initialDelaySeconds, address initialOwner) {
        delay = initialDelaySeconds;
        _transferOwnership(initialOwner == address(0) ? msg.sender : initialOwner);
        // opcionalmente, o owner também é proposer por padrão
        isProposer[owner()] = true;
        emit ProposerSet(owner(), true);
        emit DelayUpdated(delay);
    }

    modifier onlyProposer() {
        require(isProposer[msg.sender], "not proposer");
        _;
    }

    function setProposer(address who, bool allowed) external onlyOwner {
        isProposer[who] = allowed;
        emit ProposerSet(who, allowed);
    }

    function setDelay(uint256 newDelay) external onlyOwner {
        delay = newDelay;
        emit DelayUpdated(newDelay);
    }

    /// @notice Cria uma operação “time-locked”.
    function propose(address target, uint256 value, bytes calldata data) external onlyProposer returns (bytes32 opId) {
        require(target != address(0), "bad target");
        opId = keccak256(abi.encode(target, value, data, block.timestamp, address(this)));
        require(!ops[opId].exists, "dup");
        uint256 eta = block.timestamp + delay;
        ops[opId] = Operation({target: target, value: value, data: data, eta: eta, executed: false, exists: true});
        emit Proposed(opId, target, value, data, eta);
    }

    /// @notice Cancela uma operação antes da execução.
    function cancel(bytes32 opId) external onlyOwner {
        Operation storage op = ops[opId];
        require(op.exists && !op.executed, "not cancellable");
        delete ops[opId];
        emit Cancelled(opId);
    }

    /// @notice Executa após o timelock.
    function execute(bytes32 opId) external payable {
        Operation storage op = ops[opId];
        require(op.exists && !op.executed, "bad op");
        require(block.timestamp >= op.eta, "too early");

        op.executed = true;
        (bool ok, ) = op.target.call{value: op.value}(op.data);
        emit Executed(opId, ok);
        require(ok, "call failed");
    }

    // ---- Helpers específicos para políticas do Executor (facilitam a UX) ----

    function encodeSetWhitelist(address target, bool allowed) external pure returns (bytes memory) {
        return abi.encodeWithSelector(IExecutorPolicy.setWhitelist.selector, target, allowed);
    }

    function encodeSetCap(address target, uint256 maxValue) external pure returns (bytes memory) {
        return abi.encodeWithSelector(IExecutorPolicy.setCap.selector, target, maxValue);
    }
}
