#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Build Solana program (Anchor)"
cd programs/solana/bridge_adapter
anchor build

echo "[2/4] Deploy Solana program"
anchor deploy

cd ../../../

echo "[3/4] Compile EVM contracts"
# Ajuste para Hardhat ou Foundry conforme seu toolchain
if [ -f "foundry.toml" ]; then
  forge build
elif [ -f "hardhat.config.ts" ] || [ -f "hardhat.config.js" ]; then
  npx hardhat compile
else
  echo ">> Nenhum toolchain EVM detectado (Foundry/Hardhat). Pulei esta etapa."
fi

echo "[4/4] Done."
