import sys
from downloader import ContractDownloader
from comparer import Comparer

#TODO: get from args
alchemy_url = 'ALCHEMY_URL'
etherscan_api_key = 'ETHERSCAN_API_KEY'

contract_addresses = sys.argv[1:]
with ContractDownloader(etherscan_api_key, alchemy_url) as downloader:
    Comparer(downloader=downloader)(contract_addresses=contract_addresses)
