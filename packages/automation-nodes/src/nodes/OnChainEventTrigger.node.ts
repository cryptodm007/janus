import type { INodeType, INodeTypeDescription, ITriggerFunctions } from 'n8n-workflow';
import { EVM_DEFAULTS, SOLANA_DEFAULTS } from '../utils/chainConfig';
import { listenEvmEvents, pollSolanaSignatures } from '../utils/eventListener';

export class OnChainEventTrigger implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'On-Chain Event Trigger',
    name: 'onChainEventTrigger',
    group: ['trigger'],
    version: 1,
    description: 'Dispara workflow ao detectar um evento on-chain (EVM por topic ou Solana por assinaturas)',
    defaults: { name: 'On-Chain Event' },
    inputs: [],
    outputs: ['main'],
    properties: [
      {
        displayName: 'Chain Type',
        name: 'chainType',
        type: 'options',
        options: [
          { name: 'EVM', value: 'evm' },
          { name: 'Solana', value: 'solana' },
        ],
        default: 'evm',
      },
      // EVM
      {
        displayName: 'EVM Network',
        name: 'evmNetwork',
        type: 'options',
        options: [
          { name: 'Base Sepolia', value: 'base-sepolia' },
          { name: 'Base Mainnet', value: 'base-mainnet' },
          { name: 'EVM Custom (env)', value: 'evm-custom' },
        ],
        default: 'base-sepolia',
        displayOptions: { show: { chainType: ['evm'] } },
      },
      {
        displayName: 'Contract Address',
        name: 'evmAddress',
        type: 'string',
        default: '',
        displayOptions: { show: { chainType: ['evm'] } },
      },
      {
        displayName: 'Event Signature or Topic (e.g. Transfer(address,address,uint256) ou 0xddf252ad...)',
        name: 'evmTopic',
        type: 'string',
        default: '',
        displayOptions: { show: { chainType: ['evm'] } },
      },
      // Solana
      {
        displayName: 'Solana Network',
        name: 'solNetwork',
        type: 'options',
        options: [
          { name: 'Devnet', value: 'solana-devnet' },
          { name: 'Mainnet', value: 'solana-mainnet' },
          { name: 'Custom (env)', value: 'solana-custom' },
        ],
        default: 'solana-devnet',
        displayOptions: { show: { chainType: ['solana'] } },
      },
      {
        displayName: 'Address (ProgramID/Account)',
        name: 'solAddress',
        type: 'string',
        default: '',
        displayOptions: { show: { chainType: ['solana'] } },
      },
      {
        displayName: 'Polling Interval (ms)',
        name: 'solInterval',
        type: 'number',
        default: 5000,
        displayOptions: { show: { chainType: ['solana'] } },
      },
    ],
  };

  async trigger(this: ITriggerFunctions) {
    const chainType = this.getNodeParameter('chainType', 0) as 'evm' | 'solana';

    if (chainType === 'evm') {
      const net = this.getNodeParameter('evmNetwork', 0) as 'base-sepolia' | 'base-mainnet' | 'evm-custom';
      const cfg = EVM_DEFAULTS[net];
      if (!cfg.rpcWs) throw new Error('Missing JANUS_EVM_RPC_WS');

      const address = this.getNodeParameter('evmAddress', 0) as string;
      const topic = this.getNodeParameter('evmTopic', 0) as string;

      const close = await listenEvmEvents(
        cfg.rpcWs,
        address,
        topic,
        async (log) => {
          this.emit([this.helpers.returnJsonArray([{ chain: 'evm', network: net, log }])]);
        },
        (err) => this.emitError(err),
      );

      async function closeFunction() { close(); }
      return { closeFunction };
    }

    // Solana
    const net = this.getNodeParameter('solNetwork', 0) as 'solana-devnet' | 'solana-mainnet' | 'solana-custom';
    const cfg = SOLANA_DEFAULTS[net];
    if (!cfg.rpcHttp) throw new Error('Missing JANUS_SOLANA_RPC_HTTP');

    const address = this.getNodeParameter('solAddress', 0) as string;
    const interval = this.getNodeParameter('solInterval', 0) as number;

    const close = await pollSolanaSignatures(
      cfg.rpcHttp,
      address,
      interval,
      async (signature) => {
        this.emit([this.helpers.returnJsonArray([{ chain: 'solana', network: net, signature }])]);
      },
      (err) => this.emitError(err),
    );

    async function closeFunction() { close(); }
    return { closeFunction };
  }
}
