import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { providerRequest } from '../utils/web3Provider';

const DEFAULT_EXEC_PATH = 'v3/transaction/contract/execute';

export class ProviderContractWrite implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Web3 API - Contract Write',
    name: 'providerContractWrite',
    group: ['transform'],
    version: 1,
    description: 'Executa função de contrato via API externa',
    defaults: { name: 'Contract Write' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Endpoint Path', name: 'endpointPath', type: 'string', default: DEFAULT_EXEC_PATH },
      { displayName: 'Network', name: 'network', type: 'string', default: 'base-sepolia' },
      { displayName: 'Contract Address', name: 'contractAddress', type: 'string', default: '', required: true },
      { displayName: 'ABI (JSON)', name: 'abi', type: 'json', default: '[]' },
      { displayName: 'Function', name: 'functionName', type: 'string', default: '', required: true },
      { displayName: 'Args (JSON array)', name: 'args', type: 'json', default: '[]' },
      { displayName: 'Value (ETH, opcional)', name: 'valueEth', type: 'string', default: '0' },
      { displayName: 'Gas Limit (opcional)', name: 'gasLimit', type: 'number', default: 0 },
      { displayName: 'Max Fee Per Gas (gwei, opcional)', name: 'maxFeePerGasGwei', type: 'number', default: 0 },
      { displayName: 'Max Priority Fee Per Gas (gwei, opcional)', name: 'maxPriorityFeePerGasGwei', type: 'number', default: 0 },
      { displayName: 'Raw Extra Body (JSON, opcional)', name: 'extraBody', type: 'json', default: '{}' },
    ],
  };

  async execute(this: IExecuteFunctions) {
    const items = this.getInputData();
    const out: any[] = [];

    for (let i = 0; i < items.length; i++) {
      const endpointPath = this.getNodeParameter('endpointPath', i) as string;
      const network = this.getNodeParameter('network', i) as string;
      const contractAddress = this.getNodeParameter('contractAddress', i) as string;
      const abi = this.getNodeParameter('abi', i) as any;
      const functionName = this.getNodeParameter('functionName', i) as string;
      const args = this.getNodeParameter('args', i) as any[];
      const valueEth = this.getNodeParameter('valueEth', i) as string;
      const gasLimit = this.getNodeParameter('gasLimit', i) as number;
      const maxFeePerGasGwei = this.getNodeParameter('maxFeePerGasGwei', i) as number;
      const maxPriorityFeePerGasGwei = this.getNodeParameter('maxPriorityFeePerGasGwei', i) as number;
      const extraBody = this.getNodeParameter('extraBody', i) as any;

      const body: any = {
        network,
        to: contractAddress,
        abi,
        functionName,
        params: args || [],
        value: valueEth && valueEth !== '0' ? `${valueEth} ETH` : undefined,
        gasLimit: gasLimit > 0 ? gasLimit : undefined,
        maxFeePerGas: maxFeePerGasGwei > 0 ? `${maxFeePerGasGwei} gwei` : undefined,
        maxPriorityFeePerGas: maxPriorityFeePerGasGwei > 0 ? `${maxPriorityFeePerGasGwei} gwei` : undefined,
        ...extraBody,
      };

      const res = await providerRequest<any>(endpointPath, 'POST', body);
      out.push({ json: { request: body, response: res } });
    }

    return this.prepareOutputData(out);
  }
}
