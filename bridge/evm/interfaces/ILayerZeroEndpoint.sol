// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @notice Interface mínima do endpoint LayerZero (v2-like simplificado para fins de integração).
/// @dev Esta interface NÃO é oficial. Serve como "adapter boundary" para o nosso IBridgeAdapter.
///      Ao integrar com a versão real, substitua pelos pacotes/ABIs oficiais do provider.
interface ILayerZeroEndpoint {
    /// @notice Envia mensagem cross-chain para o endpoint do destino.
    /// @param dstEid  ID da chain remota segundo o provedor (não confundir com EVM chainId)
    /// @param payload Bytes arbitrários da mensagem
    /// @param options Bytes com opções de gas/execução específicas do provider
    /// @param refundAddress Onde devolver fundos excedentes de fee
    /// @return messageId Identificador único da mensagem no provedor
    function send(
        uint32 dstEid,
        bytes calldata payload,
        bytes calldata options,
        address refundAddress
    ) external payable returns (bytes32 messageId);

    /// @notice Deve ser chamado pelo provider/endpoint remoto para entregar mensagem recebida.
    /// @dev Em implementações reais, isto é chamado internamente pelo endpoint do provedor.
    function deliver(bytes32 messageId, bytes calldata payload, bytes calldata proof) external;

    /// @notice Consulta status de finalidade (mock/simplificado).
    function getMessageStatus(bytes32 messageId) external view returns (uint8); // 0=PENDING,1=FINALIZED,2=FAILED

    /// @notice Evento disparado quando o endpoint de fato recebe/entrega uma mensagem ao app.
    event LzMessageDelivered(bytes32 indexed messageId, bytes payload);
}
