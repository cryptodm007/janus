import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";

const config: HardhatUserConfig = {
  solidity: "0.8.24",
  networks: {
    baseSepolia: { url: process.env.RPC_BASE || "", accounts: [process.env.DEPLOYER_KEY || ""] }
  }
};
export default config;
