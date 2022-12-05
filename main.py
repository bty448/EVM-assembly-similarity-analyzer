import os
import sys
from dotenv import load_dotenv
from downloader import ContractDownloader
from comparer import Comparer


def main():
    load_dotenv()

    node_url = os.getenv('NODE_URL')
    etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')

    if not node_url or not etherscan_api_key:
        print('NODE_URL and ETHERSCAN_API_KEY must be set in .env')
        sys.exit(1)

    contract_addresses = sys.argv[1:]
    with ContractDownloader(etherscan_api_key, node_url) as downloader:
        Comparer(downloader).compare(contract_addresses)


if __name__ == '__main__':
    main()
