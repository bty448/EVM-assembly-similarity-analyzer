import os
import sys
from dotenv import load_dotenv

from contract_manager import ContractManager
from contract_manager.downloader import ContractDownloader
from comparer import Comparer


def main():
    load_dotenv()

    node_url = os.getenv('NODE_URL')
    etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')

    if not node_url or not etherscan_api_key:
        print('NODE_URL and ETHERSCAN_API_KEY must be set in .env')
        sys.exit(1)

    contract_addresses = sys.argv[1:]
    with Comparer(ContractManager(ContractDownloader(etherscan_api_key, node_url))) as comparer:
        comparer.compare(contract_addresses)


if __name__ == '__main__':
    main()
