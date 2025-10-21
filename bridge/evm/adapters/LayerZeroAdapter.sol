// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { IBridgeAdapter } from "../interfaces/IBridgeAdapter.sol";
import { ILayerZeroEndpoint } from "../interfaces/ILayerZeroEndpoint.sol";
import { Types } from "../libs/Types.sol";

/// @title LayerZeroAdapter (skeleton)
/// @notice Implementação de IBridgeAdapter apoiada em um endpoint LayerZero-like.
/// @dev Substitua a interface pelo pacote oficial ao integrar na infra real.
contract LayerZeroAdapter is IBridgeAdapter {
    ILayerZeroEndpoint public endpoint;
    address public registry; // contrato JanusRegistry autorizado a receber callbacks
    address public admin;

    mapping(bytes32 => Types.Finality) public messageStatus;

    event EndpointSet(address indexed endpoint);
    event RegistrySet(address indexed registry);

    modifier onlyAdmin() {
        require(msg.sender == admin, "only admin");
        _;
    }

    constructor(address _endpoint, address _registry) {
        admin = msg.sender;
        endpoint = ILayerZeroEndpoint(_endpoint);
        registry  = _registry;
        emit EndpointSet(_endpoint);
        emit RegistrySet(_registry);
    }

    function setEndpoint(address _endpoint) external onlyAdmin {
        endpoint = ILayerZeroEndpoint(_endpoint);
        emit EndpointSet(_endpoint);
    }

    function setRegistry(address _registry) external onlyAdmin {
        registry = _registry;
        emit RegistrySet(_registry);
    }

    /// @notice Converte nosso dstChainId em dstEid do provider (mapeamento governado/externo).
    function _toProviderEid(uint64 dstChainId) internal pure returns (uint32) {
        // TODO: mapear adequadamente. Placeholder: truncamento.
        return uint32(dstChainId);
    }

    function sendMessage(
        uint64 dstChainId,
        bytes calldata dstAddress, // opcionalmente embutido no payload, conforme design
        bytes calldata payload,
        uint256 /*gasLimitHint*/
    ) external override returns (bytes32 messageId) {
        // Em providers reais, options inclui gas, executor, etc.
        bytes memory options = bytes("");
        uint32 dstEid = _toProviderEid(dstChainId);
        messageId = endpoint.send{value: msg.value}(dstEid, _compose(dstAddress, payload), options, msg.sender);
        messageStatus[messageId] = Types.Finality.PENDING;

        emit MessageSent(messageId, dstChainId, dstAddress, uint64(block.number), uint64(block.timestamp + 1 hours));
    }

    function sendToken(
        uint64 dstChainId,
        bytes calldata dstAddress,
        address token,
        uint256 amount
    ) external override returns (bytes32 transferId) {
        // Em integração real, você chamaria o endpoint do token bridge específico (OFT/Token adapters).
        // Aqui apenas emitimos eventos para manter a telemetria.
        transferId = keccak256(abi.encodePacked("LZ-TOK", msg.sender, dstChainId, dstAddress, token, amount, block.number));
        emit TokenTransferInitiated(transferId, token, msg.sender, dstAddress, amount);
        // A finalização real vem via callback do provider; aqui mantemos simples:
        emit TokenTransferFinalized(transferId, Types.Finality.FINALIZED);
    }

    function getFinality(bytes32 messageId) external view override returns (Types.Finality) {
        return messageStatus[messageId];
    }

    function verifyMessage(bytes32 /*messageId*/, bytes calldata /*proof*/) external pure override returns (bool) {
        // Em produção: validar merkle/assinaturas do provider.
        return true;
    }

    /// @notice Handler que seria chamado pelo endpoint provider quando a mensagem for entregue.
    /// @dev Em providers reais, existe uma interface de "app" que o endpoint chama diretamente.
    function onProviderDeliver(bytes32 messageId, bytes calldata payload, bytes calldata proof) external {
        require(msg.sender == address(endpoint), "only endpoint");
        messageStatus[messageId] = Types.Finality.FINALIZED;
        emit MessageFinalized(messageId, Types.Finality.FINALIZED);

        // Decodifica jobId + success da execução remota (design do payload fica a seu cargo)
        (bytes32 jobId, bool success) = _decodeAck(payload);

        // Callback no Registry
        (bool ok, ) = registry.call(abi.encodeWithSignature(
            "onMessageReceived(bytes32,bool,bytes)", jobId, success, proof
        ));
        require(ok, "registry callback failed");
    }

    function _compose(bytes calldata dstAddress, bytes calldata payload) internal pure returns (bytes memory out) {
        // Formato simples: [ dst_len | dst_addr | payload ]
        out = abi.encode(dstAddress, payload);
    }

    function _decodeAck(bytes calldata payload) internal pure returns (bytes32 jobId, bool success) {
        // Compatível com _compose do lado remoto: defina seu formato canônico
        (bytes memory dstAddrIgnored, bytes memory inner) = abi.decode(payload, (bytes, bytes));
        // Exemplo: ack = abi.encode(jobId, success)
        (jobId, success) = abi.decode(inner, (bytes32, bool));
    }
}
