import json
import operator
from downloader import ContractDownloader
from .hasher import Hasher
from .diff import find_diff, is_significant_diff


class Comparer:
    def __init__(self, downloader: ContractDownloader):
        self.downloader = downloader
        self.hasher = Hasher()

    def compare(self, contract_addresses: list[str]) -> None:
        self._download_contracts(contract_addresses=contract_addresses)

        # {address -> [{signature, function_assembly}]}
        funcs_dict = {}

        for address, contract_data in self.contracts_data.items():
            # plan:

            # 1. get all functions hash codes from abi
            signatures, method_ids = self._get_functions_info(contract_data['abi'])

            # 2. find occurrences in assembly file and find corresponding position of JUMPDEST in code
            functions_jumpdests = self._find_jumpdests_of_functions(
                assembly=contract_data['assembly'],
                method_ids=method_ids
            )

            funcs_data = list(zip(functions_jumpdests, signatures, method_ids))
            funcs_data.sort(key=operator.itemgetter(0))

            # 3. split assembly by functions and obtain a dict
            # whereby address of the contract we get the list of functions
            funcs_dict[address] = self._split_assembly_on_funcs(
                assembly=contract_data['assembly'],
                funcs_data=funcs_data
            )

        self._compare_contracts_functions(contract_addresses=contract_addresses, funcs_dict=funcs_dict)

    def _download_contracts(self, contract_addresses: list[str]) -> None:
        self.contracts_data = {}

        # TODO: add caching
        for address in contract_addresses:
            self.downloader.download(address=address)
            contract_dir = self.downloader.get_out_dir(address=address)

            with open(contract_dir + "/abi.json") as abi:
                with open(contract_dir + "/assembly") as assembly:
                    self.contracts_data[address] = {
                        'abi': json.load(abi),
                        'assembly': assembly.read().splitlines(),
                    }

    def _get_functions_info(self, abi: dict) -> (list[str], list[str]):
        signatures = []
        method_ids = []

        for entry in abi:
            if entry['type'] == 'function':
                args = ','.join([arg['type'] for arg in entry['inputs']])
                signature = f"{entry['name']}({args})"
                method_id = '0x' + self.hasher.get_method_id(signature)

                signatures.append(signature)
                method_ids.append(method_id)

        return signatures, method_ids

    def _find_jumpdests_of_functions(self, assembly: list[str], method_ids: list[str]) -> list[int]:
        jumpdests = []

        address_to_line = {}
        for i in range(len(assembly)):
            line = assembly[i]
            address_to_line[int(line.split()[0])] = i

        for method_id in method_ids:
            for i in range(len(assembly)):
                line = assembly[i]
                if line == '':
                    continue
                split_line = line.split()
                if len(split_line) < 3:
                    continue
                (address, opcode, arg) = line.split()
                if opcode == 'PUSH4' and arg == method_id:
                    if i + 3 >= len(assembly):
                        # no jump
                        continue
                    expected_jump = assembly[i + 3].split()[1]
                    if expected_jump != 'JUMP' and expected_jump != 'JUMPI':
                        # no jump
                        continue
                    push_address = assembly[i + 2].split()
                    if len(push_address) < 3:
                        # no push
                        continue
                    (push_address, push_opcode, dest_address_hex) = push_address
                    if push_opcode != 'PUSH2':
                        # no push
                        continue
                    dest_address = int(dest_address_hex, base=16)
                    if dest_address not in address_to_line:
                        # no such address
                        continue
                    jumpdests.append(address_to_line[dest_address])
                    break  # search only first occurrence
            else:
                # no occurrence found
                jumpdests.append(-1)

        return jumpdests

    def _split_assembly_on_funcs(self, assembly: list[str], funcs_data: list[tuple[int, str, str]]) -> list[dict]:
        funcs = []

        milestones = funcs_data + [(len(assembly), '', '')]

        for i in range(1, len(milestones)):
            (start_line, signature, _) = milestones[i - 1]
            if start_line == -1:
                continue
            (end_line, _, _) = milestones[i]
            funcs.append({
                'signature': signature,
                'function_assembly': assembly[start_line + 1: end_line]
            })

        return funcs

    def _compare_contracts_functions(self, contract_addresses: list[str], funcs_dict: dict) -> None:
        for i in range(1, len(contract_addresses)):
            for j in range(i):
                addresses = (contract_addresses[i], contract_addresses[j])
                funcs_with_signature = (funcs_dict[addresses[0]], funcs_dict[addresses[1]])

                used = (set(), set())

                for k in range(len(funcs_with_signature[0])):
                    for r in range(len(funcs_with_signature[1])):
                        funcs = (funcs_with_signature[0][k], funcs_with_signature[1][r])

                        for m in range(2):
                            if funcs[m]['signature'] in used[m]:
                                continue  # TODO: lol, it's continue from inner loop

                        diff = find_diff(funcs)
                        if not is_significant_diff(diff):
                            print('Found similar functions in contracts:')
                            for m in range(2):
                                print(f"\t{addresses[m]}: {funcs[m]['signature']}")
                            print()

                        for m in range(2):
                            used[m].add(funcs[m]['signature'])
