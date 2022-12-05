import json
import os
from time import sleep

from requests.sessions import Session
from web3 import Web3, HTTPProvider

from .network import Network
from .downloader_exception import DownloaderException
from disassembler import disassemble


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
        """
        :param etherscan_api_key: The Etherscan API key
        :param node_url: The URL of the Ethereum node
        :param output_dir: The output directory
        :param network: The network, defaults to mainnet
        """
        self.api_key = etherscan_api_key
        self.web3 = Web3(HTTPProvider(node_url))
        self.output_dir = output_dir
        self.network = network
        self.endpoint = _get_endpoint(network)
        self.session = Session()

        if not self.web3.isConnected():
            raise DownloaderException('Unable to connect to node')

    def download(self, address: str) -> None:
        """
        Downloads the bytecode, source code, ABI and metadata for a contract
        :param address: The address of the contract
        :return: None
        """
        self.download_from_etherscan(address)
        self.download_bytecode(address)

    def download_bytecode(self, address: str) -> None:
        """
        Downloads the bytecode for a contract from the node
        :param address: The address of the contract
        :return: None
        """
        bytecode = self.web3.eth.get_code(address)
        self._save(address, 'bytecode', bytecode, binary=True)
        assembly = disassemble(bytecode, add_addresses=True)
        self._save(address, 'assembly', assembly)

    def download_from_etherscan(self, address: str) -> None:
        """
        Downloads the bytecode, source code, ABI and metadata for a contract from Etherscan
        :param address: The address of the contract
        :return: None
        """
        response = self.get_contract_source_code(address)
        result = response['result'][0]
        source_code = result['SourceCode']
        if source_code:
            if source_code.startswith('{{'):
                sources = json.loads(source_code[1:-1])['sources']
                for filename, source in sources.items():
                    self._save_src(address, filename, source['content'])
            else:
                self._save_src(address, 'SourceCode.sol', source_code)

        abi = result['ABI']
        if abi != 'Contract source code not verified':
            self._save(address, 'abi.json', abi)

        del result['SourceCode']
        del result['ABI']

        self._save(address, 'metadata.json', json.dumps(result, indent=4))

    def get_contract_source_code(self, address: str) -> dict:
        """
        Gets the source code for a contract from Etherscan
        :param address: The address of the contract
        :return: The source code
        """
        return self._request('getsourcecode', {'address': address})

    def get_contract_abi(self, address: str) -> dict:
        """
        Gets the ABI for a contract from Etherscan
        :param address: The address of the contract
        :return: The ABI
        """
        return self._request('getabi', {'address': address})

    def get_creation_tx_hash(self, address: str) -> dict:
        """
        Gets the transaction hash of the contract creation transaction
        :param address: The address of the contract
        :return: The transaction hash
        """
        return self._request('getcontractcreation', {'contractaddresses': address})
    
    def get_out_dir(self, address: str) -> str:
        """
        Gets the output directory for a contract
        :param address: The address of the contract
        :return: The output directory
        """
        return os.path.join(self.output_dir, self.network.value, address)

    def close(self) -> None:
        """
        Closes the downloader
        :return: None
        """
        self.session.close()

    def __enter__(self) -> 'ContractDownloader':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _request(self, action: str, params=None) -> dict:
        url = self._get_url(action, params)
        while True:
            response = self.session.get(url).json()
            if response['status'] == '1':
                return response
            if response['result'] == 'Max rate limit reached':
                sleep(1)
                continue
            raise DownloaderException(response['message'])

    def _get_url(self, action: str, params=None) -> str:
        if params is None:
            params = {}
        params['module'] = 'contract'
        params['action'] = action
        params['apikey'] = self.api_key
        return self.endpoint + '?' + '&'.join([f'{key}={value}' for key, value in params.items()])

    def _save_src(self, address: str, filename: str, content: str) -> None:
        self._save(address, filename, content, inner_dir='src')

    def _save(self, address: str, name: str, content: str, inner_dir=None, binary=False) -> None:
        contract_dir = self.get_out_dir(address)
        if inner_dir is not None:
            contract_dir = os.path.join(contract_dir, inner_dir)
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
