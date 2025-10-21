import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { Connection, PublicKey, SystemProgram, Transaction } from '@solana/web3.js';
import { SOLANA_DEFAULTS, type SolanaNetwork } from '../utils/chainConfig';

export class SolanaTransactionBuilder implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Solana Transaction Builder',
    name: 'solanaTransactionBuilder',
    group: ['transform'],
    version: 1,
    description: 'Constrói uma transação simples na Solana (transferência de lamports ou instruções custom)',
    defaults: { name: 'Solana Tx Builder' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      {
        displayName: 'Network',
        name: 'network',
        type: 'options',
        options: [
          { name: 'Devnet', value: 'solana-devnet' },
          { name: 'Mainnet', value: 'solana-mainnet' },
          { name: 'Custom (env)', value: 'solana-custom' },
        ],
        default: 'solana-devnet',
      },
      {
        displayName: 'From (PublicKey base58, usado apenas para recentBlockhash)',
        name: 'fromPubkey',
        type: 'string',
        default: '',
        description: 'A chave pública do pagador (somente para composição do tx).'
      },
      {
        displayName: 'To (PublicKey base58)',
        name: 'toPubkey',
        type: 'string',
        default: '',
        required: true,
      },
      {
        displayName: 'Lamports',
        name: 'lamports',
        type: 'number',
        default: 0,
      },
      {
        displayName: 'Add Custom Instructions (JSON array of base64/keys)?',
        name: 'custom',
        type: 'json',
        default: "[]",
        description: 'Opcional: lista de instruções custom (não assina).'
      }
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData();
    const returnData = [];

    for (let i = 0; i < items.length; i++) {
      const network = this.getNodeParameter('network', i) as SolanaNetwork;
      const cfg = SOLANA_DEFAULTS[network];
      if (!cfg.rpcHttp) throw new Error('Missing JANUS_SOLANA_RPC_HTTP or default RPC');

      const from = new PublicKey(this.getNodeParameter('fromPubkey', i) as string);
      const to = new PublicKey(this.getNodeParameter('toPubkey', i) as string);
      const lamports = this.getNodeParameter('lamports', i) as number;
      const custom = this.getNodeParameter('custom', i) as any[];

      const conn = new Connection(cfg.rpcHttp, 'confirmed');
      const { blockhash, lastValidBlockHeight } = await conn.getLatestBlockhash('finalized');

      const tx = new Transaction({
        recentBlockhash: blockhash,
        feePayer: from,
        lastValidBlockHeight,
      });

      if (lamports > 0) {
        tx.add(SystemProgram.transfer({ fromPubkey: from, toPubkey: to, lamports }));
      }

      // No exemplo simplificado, ignoramos custom base64 e assumimos instruções já montadas externamente.
      // Em produção, parseie base64/ABI/Anchor e adicione a tx.

      returnData.push({ json: { network, tx: tx.serialize({ requireAllSignatures: false }).toString('base64') } });
    }

    return this.prepareOutputData(returnData);
  }
}
