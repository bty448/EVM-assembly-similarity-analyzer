import json
import operator
from downloader import ContractDownloader
from .hasher import Hasher
from .diff import find_diff, is_significant_diff


class Comparer:
    def __init__(self, downloader: ContractDownloader):
        self.downloader = downloader
        self.hasher = Hasher()
    
    def __call__(self, contract_addresses: list = []):
        self._download_contracts(contract_addresses=contract_addresses)

        # {address -> [{signature, function_assembly}]}
        funcs_dict = {}

        for address, contract_data in self.contracts_data.items():
            #plan:

            # 1. get all funcitons hash codes from abi
            signatures, method_ids = self._get_functions_info(contract_data['abi'])

            # 2. find occurences in assembly file and find corresponding position of JUMPDEST in code
            functions_jumpdests = self._find_jumpdests_of_functions(assembly=contract_data['assembly'], method_ids=method_ids)

            funcs_data = list(zip(functions_jumpdests, signatures, method_ids))
            funcs_data.sort(key=operator.itemgetter(0))

            # 3. split assembly by functions and obtain a dict where by address of the contract we get the list of functions
            funcs_dict[address] = self._split_assembly_on_funcs(assembly=contract_data['assembly'], funcs_data=funcs_data)
        
        self._compare_contracts_functions(contract_addresses=contract_addresses, funcs_dict=funcs_dict)

    def _download_contracts(self, contract_addresses: list = []):
        self.contracts_data = {}

        #TODO: add caching
        for address in contract_addresses:
            self.downloader.download(address=address)
            contract_dir = self.downloader.get_out_dir(address=address)

            with open(contract_dir + "/abi.json") as abi:
                with open(contract_dir + "/assembly") as assembly:
                    self.contracts_data[address] = {
                        'abi':      json.load(abi),
                        'assembly': assembly.readlines(),
                    }
    
    # Returns 2 lists: list of functions' signatures and list of corresponding method ids.
    # They go in the same order
    def _get_functions_info(self, abi):
        signatures = []
        method_ids = []

        for entry in abi:
            if entry['type'] == 'function':
                signature = entry['name'] + '(' + ','.join([input['type'] for input in entry['inputs']]) + ')'
                method_id = self.hasher.get_hash(signature)

                signatures.append(signature)
                method_ids.append(method_id)

        return signatures, method_ids

    # Returns a list of lines of JUMPDESTs of functions
    def _find_jumpdests_of_functions(self, assembly, method_ids):
        jumpdests = []

        address_to_line = {}
        for i in range(len(assembly)):
            line = assembly[i]
            address_to_line[int(line.split(' ')[0])] = i

        for method_id in method_ids:
            for i in range(len(assembly)):
                line = assembly[i]
                if line.split(' ')[-1] == method_id:
                    dest_address_hex = assembly[i + 2].split(' ')[-1]
                    dest_address_dec = int(dest_address_hex[2:], base=16)
                    jumpdests.append(address_to_line[dest_address_dec])

        return jumpdests

    def _split_assembly_on_funcs(self, assembly, funcs_data):
        funcs = []

        milestones = funcs_data + [(len(assembly), '', '')]

        for i in range(1, len(milestones)):
            (start_line, signature, _) = milestones[i - 1]
            (end_line, _, _) = milestones[i]
            funcs.append({
                'signature': signature,
                'function_assembly': assembly[start_line + 1 : end_line]
            })
        
        return funcs[0:]

    def _compare_contracts_functions(self, contract_addresses, funcs_dict):
        for i in range(len(contract_addresses)):
            for j in range(i):
                addrs = (contract_addresses[i], contract_addresses[j])
                funcs_with_signature = (funcs_dict[addrs[0]], funcs_dict[addrs[1]])

                used = (set(), set())

                for k in range(len(funcs_with_signature[0])):
                    for l in range(len(funcs_with_signature[1])):
                        funcs = (funcs_with_signature[0][k], funcs_with_signature[1][l])

                        for m in range(2):
                            if used[m].contains(funcs[m]['signature']):
                                continue

                        diff = find_diff(funcs)
                        if not is_significant_diff(diff):
                            print('Found similar functions in contracts with addresses: {} and {}.'.format(addrs[0], addrs[1]))
                            for m in range(2):
                                print('Function in contract with address {}: {}'.format(addrs[k], funcs[k]['signature']))
                            print()
                        
                        for m in range(2):
                            used[m].add(funcs[m]['signature'])
