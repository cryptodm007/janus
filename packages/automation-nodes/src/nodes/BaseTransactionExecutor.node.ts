import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { ethers } from 'ethers';
import { EVM_DEFAULTS, type EvmNetwork } from '../utils/chainConfig';

export class BaseTransactionExecutor implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Base Transaction Executor',
    name: 'baseTransactionExecutor',
    group: ['transform'],
    version: 1,
    description: 'Assina e envia uma transação EVM na rede Base (ou EVM custom)',
    defaults: { name: 'Base Tx Executor' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      {
        displayName: 'Network',
        name: 'network',
        type: 'options',
        options: [
          { name: 'Base Sepolia', value: 'base-sepolia' },
          { name: 'Base Mainnet', value: 'base-mainnet' },
          { name: 'EVM Custom (env)', value: 'evm-custom' },
        ],
        default: 'base-sepolia',
      },
      {
        displayName: 'Private Key (env: JANUS_EVM_PRIVATE_KEY)',
        name: 'pkEnv',
        type: 'boolean',
        default: true,
        description: 'Se true, usa a chave da env JANUS_EVM_PRIVATE_KEY',
      },
      {
        displayName: 'Transaction (from previous node)',
        name: 'tx',
        type: 'json',
        default: "{}",
        description: 'Objeto TransactionRequest do node anterior (ou construa aqui).',
      }
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData();
    const returnData = [];

    for (let i = 0; i < items.length; i++) {
      const network = this.getNodeParameter('network', i) as EvmNetwork;
      const useEnv = this.getNodeParameter('pkEnv', i) as boolean;
      const tx = this.getNodeParameter('tx', i) as any;

      const cfg = EVM_DEFAULTS[network];
      if (!cfg.rpcHttp) throw new Error('Missing JANUS_EVM_RPC_HTTP');

      const provider = new ethers.JsonRpcProvider(cfg.rpcHttp, cfg.chainId);
      const pk = process.env.JANUS_EVM_PRIVATE_KEY;
      if (useEnv && !pk) throw new Error('Missing JANUS_EVM_PRIVATE_KEY');

      const wallet = new ethers.Wallet(pk as string, provider);

      // Se tx não veio, erro
      if (!tx || (!tx.to && !tx.data)) throw new Error('Invalid tx payload');

      // Preenche campos ausentes
      const populated = await wallet.populateTransaction({
        chainId: cfg.chainId,
        ...tx,
      });

      const sent = await wallet.sendTransaction(populated);
      const receipt = await sent.wait();

      returnData.push({ json: { hash: sent.hash, receipt } });
    }

    return this.prepareOutputData(returnData);
  }
}
