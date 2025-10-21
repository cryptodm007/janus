import type { IExecuteFunctions, INodeType, INodeTypeDescription } from 'n8n-workflow';
import { providerRequest } from '../utils/web3Provider';

// Endpoint genérico (ajuste conforme o seu provedor Web3):
const DEFAULT_DEPLOY_PATH = 'v3/smart-contract/from-bytecode';

export class ProviderContractDeploy implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Web3 API - Contract Deploy',
    name: 'providerContractDeploy',
    group: ['transform'],
    version: 1,
    description: 'Faz deploy de contrato via API externa (bytecode/ABI)',
    defaults: { name: 'Contract Deploy' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      { displayName: 'Endpoint Path', name: 'endpointPath', type: 'string', default: DEFAULT_DEPLOY_PATH },
      { displayName: 'Network (ex.: base-sepolia)', name: 'network', type: 'string', default: 'base-sepolia' },
      { displayName: 'Contract Name', name: 'contractName', type: 'string', default: 'MyContract' },
      { displayName: 'ABI (JSON)', name: 'abi', type: 'json', default: '[]' },
      { displayName: 'Bytecode (0x...)', name: 'bytecode', type: 'string', default: '', required: true },
      { displayName: 'Constructor Args (JSON array)', name: 'constructorArgs', type: 'json', default: '[]' },
      { displayName: 'From (opcional)', name: 'from', type: 'string', default: '' },
      { displayName: 'Nonce (opcional)', name: 'nonce', type: 'number', default: 0 },
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
      const contractName = this.getNodeParameter('contractName', i) as string;
      const abi = this.getNodeParameter('abi', i) as any;
      const bytecode = this.getNodeParameter('bytecode', i) as string;
      const constructorArgs = this.getNodeParameter('constructorArgs', i) as any[];
      const from = (this.getNodeParameter('from', i) as string) || undefined;
      const nonce = this.getNodeParameter('nonce', i) as number;
      const gasLimit = this.getNodeParameter('gasLimit', i) as number;
      const maxFeePerGasGwei = this.getNodeParameter('maxFeePerGasGwei', i) as number;
      const maxPriorityFeePerGasGwei = this.getNodeParameter('maxPriorityFeePerGasGwei', i) as number;
      const extraBody = this.getNodeParameter('extraBody', i) as any;

      const body: any = {
        network,
        name: contractName,
        abi,
        bytecode,
        params: constructorArgs || [],
        from,
        nonce: nonce > 0 ? nonce : undefined,
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
