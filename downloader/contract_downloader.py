import json
import os
import requests
from web3 import Web3, HTTPProvider
from pyevmasm import disassemble

from .network import Network
from .downloader_exception import DownloaderException


def _get_endpoint(network: Network) -> str:
    return f'https://{_get_endpoint_prefix(network)}.etherscan.io/api'


def _get_endpoint_prefix(network: Network) -> str:
    match network:
        case Network.MAINNET:
            return 'api'
        case Network.GOERLI:
            return 'api-goerli'
        case Network.KOVAN:
            return 'api-kovan'
        case Network.RINKEBY:
            return 'api-rinkeby'
        case Network.ROPSTEN:
            return 'api-ropsten'
        case Network.SEPOLIA:
            return 'api-sepolia'
        case _:
            raise ValueError('Invalid network')


class ContractDownloader:
    def __init__(
        self,
        etherscan_api_key: str,
        node_url: str,
        output_dir: str = 'contracts',
        network: Network = Network.MAINNET,
    ):
        self.api_key = etherscan_api_key
        self.web3 = Web3(HTTPProvider(node_url))
        self.output_dir = output_dir
        self.network = network
        self.endpoint = _get_endpoint(network)

        if not self.web3.isConnected():
            raise DownloaderException('Unable to connect to node')

    def download(self, address: str):
        self.download_from_etherscan(address)
        self.download_bytecode(address)

    def download_bytecode(self, address: str):
        bytecode = self.web3.eth.get_code(address)
        self._save(address, 'bytecode', bytecode, binary=True)
        assembly = disassemble(bytecode)
        self._save(address, 'assembly', assembly)

    def download_from_etherscan(self, address: str):
        response = self.get_contract_source_code(address)
        if response['status'] == '1':
            result = response['result'][0]
            source_code = result['SourceCode']
            if source_code:
                self._save(address, 'source_code.sol', source_code)
            abi = result['ABI']
            if abi != 'Contract source code not verified':
                self._save(address, 'abi.json', abi)
            del result['SourceCode']
            del result['ABI']
            self._save(address, 'metadata.json', json.dumps(result, indent=4))
        else:
            raise DownloaderException(response['message'])

    def get_contract_abi(self, address: str):
        url = self._get_url('getabi', {'address': address})
        response = requests.get(url)
        return response.json()

    def get_contract_source_code(self, address: str):
        url = self._get_url('getsourcecode', {'address': address})
        response = requests.get(url)
        return response.json()

    def get_creation_tx_hash(self, address: str):
        url = self._get_url('getcontractcreation', {'contractaddresses': address})
        response = requests.get(url)
        return response.json()

    def _get_url(self, action, params=None):
        if params is None:
            params = {}
        params['module'] = 'contract'
        params['action'] = action
        params['apikey'] = self.api_key
        return self.endpoint + '?' + '&'.join([f'{key}={value}' for key, value in params.items()])

    def _save(self, address, name, content, binary=False):
        contract_dir = os.path.join(self.output_dir, self.network.value, address)
        if not os.path.exists(contract_dir):
            os.makedirs(contract_dir)
        path = os.path.join(contract_dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if binary:
            file = open(path, 'wb')
        else:
            file = open(path, 'w', newline='')
        with file:
            file.write(content)
