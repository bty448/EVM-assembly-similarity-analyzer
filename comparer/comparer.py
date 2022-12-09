import operator

from pyevmasm import Instruction

from contract_manager import ContractManager
from .hash_utils import get_method_id
from .diff_utils import find_diff, is_significant_diff


class Comparer:
    def __init__(self, manager: ContractManager):
        self.manager = manager

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.__exit__(exc_type, exc_val, exc_tb)

    def compare(self, contract_addresses: list[str]) -> None:
        # {address -> [{signature, function_assembly}]}
        funcs_dict = {}

        for address in set(contract_addresses):
            # plan:

            abi = self.manager.get_abi(address)
            assembly = self.manager.get_assembly(address)

            # 1. get all functions hash codes from abi
            signatures, method_ids = self._get_functions_info(abi)

            # 2. find occurrences in assembly file and find corresponding position of JUMPDEST in code
            functions_jumpdests = self._find_jumpdests_of_functions(assembly=assembly, method_ids=method_ids)

            funcs_data = list(zip(functions_jumpdests, signatures, method_ids))
            funcs_data.sort(key=operator.itemgetter(0))

            # 3. split assembly by functions and obtain a dict
            # whereby address of the contract we get the list of functions
            funcs_dict[address] = self._split_assembly_on_funcs(
                assembly=assembly,
                funcs_data=funcs_data
            )

        self._compare_contracts_functions(contract_addresses=contract_addresses, funcs_dict=funcs_dict)

    def _get_functions_info(self, abi: list) -> (list[str], list[int]):
        signatures = []
        method_ids = []

        for entry in abi:
            if entry['type'] == 'function':
                args = ','.join([arg['type'] for arg in entry['inputs']])
                signature = f"{entry['name']}({args})"
                method_id = int(get_method_id(signature), base=16)

                signatures.append(signature)
                method_ids.append(method_id)

        return signatures, method_ids

    def _find_jumpdests_of_functions(self, assembly: list[Instruction], method_ids: list[int]) -> list[int]:
        # Header pattern:
        # PUSH4 method_id
        # EQ | LT | GT
        # PUSH2 method_address
        # JUMPI
        # PUSH2 fallback_address
        # JUMP
        jumpdests = []

        # TODO: find fallbacks
        address_to_line = {instruction.pc: i for i, instruction in enumerate(assembly)}

        for method_id in method_ids:
            for i, instruction in enumerate(assembly):
                if instruction.name != 'PUSH4' or instruction.operand != method_id:
                    continue
                if i + 3 >= len(assembly):
                    # no jump
                    continue
                expected_jump = assembly[i + 3]
                if expected_jump.name != 'JUMP' and expected_jump.name != 'JUMPI':
                    # no jump
                    continue
                push_address = assembly[i + 2]
                if push_address.name != 'PUSH2':
                    # no push
                    continue
                dest_address = push_address.operand
                if dest_address not in address_to_line:
                    # no such address
                    continue
                jumpdests.append(address_to_line[dest_address])
                break  # search only first occurrence
            else:
                # no occurrence found
                jumpdests.append(-1)

        return jumpdests

    def _split_assembly_on_funcs(self, assembly: list[Instruction], funcs_data: list[(int, str, str)]) -> list[dict]:
        funcs = []

        milestones = funcs_data + [(len(assembly), '', '')]

        for i in range(1, len(milestones)):
            (start_line, signature, _) = milestones[i - 1]
            if start_line == -1:
                continue
            (end_line, _, _) = milestones[i]
            funcs.append({
                'signature': signature,
                'function_assembly': '\n'.join(map(str, assembly[start_line + 1: end_line]))
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

                        # TODO: why we skip function with same signature?
                        if any([funcs[m]['signature'] in used[m] for m in range(2)]):
                            continue

                        diff = find_diff(funcs)

                        # TODO: add parameter to control diff threshold
                        if not is_significant_diff(diff):
                            print('Found similar functions in contracts:')
                            for m in range(2):
                                print(f"\t{addresses[m]}: {funcs[m]['signature']}")
                            print()

                        for m in range(2):
                            used[m].add(funcs[m]['signature'])
