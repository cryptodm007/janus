// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Types } from "../libs/Types.sol";

/// @title IBridgeAdapter – Interface de adaptação a provedores de ponte Base↔Solana
/// @notice Implementações concretas (e.g., ProviderXAdapter) devem cumprir esta interface e expor eventos/auditoria.
interface IBridgeAdapter {
    /// @dev emitido quando mensagem é enviada ao provedor
    event MessageSent(bytes32 indexed messageId, uint64 indexed dstChainId, bytes indexed dstAddress, uint64 nonce, uint64 deadline);
    /// @dev emitido quando ack de mensagem é recebido do provedor
    event MessageFinalized(bytes32 indexed messageId, Types.Finality finalityStatus);

    /// @dev emitido quando transferência de token é iniciada
    event TokenTransferInitiated(bytes32 indexed transferId, address indexed token, address indexed from, bytes toAddress, uint256 amount);
    /// @dev emitido quando transferência de token é finalizada
    event TokenTransferFinalized(bytes32 indexed transferId, Types.Finality finalityStatus);

    function sendMessage(
        uint64 dstChainId,
        bytes calldata dstAddress,
        bytes calldata payload,
        uint256 gasLimitHint
    ) external returns (bytes32 messageId);

    function sendToken(
        uint64 dstChainId,
        bytes calldata dstAddress,
        address token,
        uint256 amount
    ) external returns (bytes32 transferId);

    function getFinality(bytes32 messageId) external view returns (Types.Finality);

    function verifyMessage(bytes32 messageId, bytes calldata proof) external view returns (bool);
}
