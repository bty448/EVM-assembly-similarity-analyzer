import os
import sys
import argparse
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

    parser = argparse.ArgumentParser(description='Find similar functions in smart contracts.')
    parser.add_argument('-c', '--contracts', nargs='+', metavar='ADDRESS',
                        required=False,
                        help='Contracts addresses in format 0x*hex*. At least 2 contracts addresses must be specified.')
    parser.add_argument('-p', '--contracts-path', metavar='PATH',
                        required=False,
                        help='Path to the file, where contracts addresses are stored. Format of each line in the file is 0x*hex*. '
                        + 'At least 2 contracts addresses must be specified.')
    parser.add_argument('-n', '--no-operands', action='store_true',
                        required=False,
                        help='Compare contracts without checking the operands.')
    parser.add_argument('-d', '--diff-percentage', metavar='DIFF_PERCENTAGE', type=int,
                        choices=range(0, 100), default=0, required=False,
                        help='Upperbound for diff of the similar functions.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        required=False,
                        help='Print to the console all the debug info.')

    args = parser.parse_args()

    contracts_addresses = []
    if args.contracts_path is not None:
        with open(args.contracts_path, 'r') as file:
            for line in file.readlines():
                while line.endswith('\n') or line.endswith('\r'):
                    line = line[:-1]
                contracts_addresses.append(line)
    
    if args.contracts is not None:
        contracts_addresses += args.contracts
    
    if len(contracts_addresses) < 2:
        print('Specify contracts to check either using addresses explicitly, or using a file with addresses. Check --help for usage info.')
    
    no_operands = args.no_operands
    verbose = args.verbose
    diff_percentage = args.diff_percentage

    with Comparer(ContractManager(ContractDownloader(etherscan_api_key, node_url)), no_operands, diff_percentage, verbose) as comparer:
        comparer.compare(contracts_addresses)


if __name__ == '__main__':
    main()
