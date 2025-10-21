// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { IBridgeAdapter } from "../interfaces/IBridgeAdapter.sol";
import { Types } from "../libs/Types.sol";

/// @title MockBridgeAdapter
/// @notice Adapter de desenvolvimento local. Não usa nenhum provedor externo.
///         Simula envio e confirmação de mensagens/transferências para testes de ponta-a-ponta.
///         Útil para integração com o JanusRegistry e com o programa Solana local/devnet.
contract MockBridgeAdapter is IBridgeAdapter {
    address public registry; // contrato autorizado a receber callbacks (JanusRegistry)
    address public admin;

    struct MsgInfo {
        Types.Finality finality;
        bytes payload;
        bytes dstAddress;
        uint64 dstChainId;
    }

    mapping(bytes32 => MsgInfo) internal _messages;

    event RegistrySet(address indexed registry);

    modifier onlyAdmin() {
        require(msg.sender == admin, "only admin");
        _;
    }

    constructor(address _registry) {
        admin = msg.sender;
        registry = _registry;
        emit RegistrySet(_registry);
    }

    function setRegistry(address _registry) external onlyAdmin {
        registry = _registry;
        emit RegistrySet(_registry);
    }

    function sendMessage(
        uint64 dstChainId,
        bytes calldata dstAddress,
        bytes calldata payload,
        uint256 /*gasLimitHint*/
    ) external override returns (bytes32 messageId) {
        // messageId determinístico simples
        messageId = keccak256(abi.encodePacked(msg.sender, dstChainId, dstAddress, payload, block.number));
        _messages[messageId] = MsgInfo({
            finality: Types.Finality.PENDING,
            payload: payload,
            dstAddress: dstAddress,
            dstChainId: dstChainId
        });

        emit MessageSent(messageId, dstChainId, dstAddress, uint64(block.number), uint64(block.timestamp + 1 hours));
    }

    function sendToken(
        uint64 dstChainId,
        bytes calldata dstAddress,
        address token,
        uint256 amount
    ) external override returns (bytes32 transferId) {
        transferId = keccak256(abi.encodePacked("TOK", msg.sender, dstChainId, dstAddress, token, amount, block.number));
        emit TokenTransferInitiated(transferId, token, msg.sender, dstAddress, amount);
        // No mock, consideramos finalizado imediatamente
        emit TokenTransferFinalized(transferId, Types.Finality.FINALIZED);
    }

    function getFinality(bytes32 messageId) external view override returns (Types.Finality) {
        return _messages[messageId].finality;
    }

    function verifyMessage(bytes32 /*messageId*/, bytes calldata /*proof*/) external pure override returns (bool) {
        // Mock: sempre true. Em produção, verificar assinatura/merkle/commit do provedor.
        return true;
    }

    /// @notice Função de teste que "finaliza" a mensagem e chama o JanusRegistry.onMessageReceived
    /// @dev Use em ambientes locais: após confirmar a execução no destino (off-chain), finalize aqui.
    function finalizeMessage(bytes32 jobId, bytes32 messageId, bool success, bytes calldata proof) external {
        require(registry != address(0), "registry not set");
        _messages[messageId].finality = Types.Finality.FINALIZED;

        emit MessageFinalized(messageId, Types.Finality.FINALIZED);
        // callback no registry
        (bool ok, ) = registry.call(abi.encodeWithSignature(
            "onMessageReceived(bytes32,bool,bytes)", jobId, success, proof
        ));
        require(ok, "registry callback failed");
    }
}
