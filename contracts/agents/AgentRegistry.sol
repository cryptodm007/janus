// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract AgentRegistry is ERC721, Ownable {
    uint256 public nextId;
    mapping(uint256 => string) public agentURI;

    constructor() ERC721("Janus Agent", "JAGENT") Ownable(msg.sender) {}

    function registerAgent(address to, string memory _uri) external onlyOwner returns (uint256) {
        uint256 id = ++nextId;
        _mint(to, id);
        agentURI[id] = _uri;
        return id;
    }

    function setAgentURI(uint256 id, string memory _uri) external onlyOwner {
        agentURI[id] = _uri;
    }
}
