import operator

from contract_manager import ContractManager
from .comparer_utils import *
from .diff_utils import SimilarFinder


class Comparer:
    def __init__(self, manager: ContractManager, no_operands=False, diff_percentage=0):
        self.manager = manager
        self.no_operands = no_operands
        self.diff_percentage = diff_percentage

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.__exit__(exc_type, exc_val, exc_tb)

    def compare(self, contract_addresses: list[str]) -> None:
        # {address -> [{signature, function_assembly}]}
        funcs_dict = {}
        assembly_dict = {}
        address_to_line_dict = {}

        for address in set(contract_addresses):
            # plan:

            abi = self.manager.get_abi(address)
            assembly = self.manager.get_assembly(address)
            address_to_line = {instruction.pc: i for i, instruction in enumerate(assembly)}

            assembly_dict[address] = assembly
            address_to_line_dict[address] = address_to_line

            # 1. get all functions hash codes from abi
            signatures, method_ids = get_functions_info(abi)

            # 2. find occurrences in assembly file and find corresponding position of JUMPDEST in code
            functions_jumpdests = find_jumpdests_of_functions(assembly, address_to_line, method_ids)
            funcs_data = list(zip(functions_jumpdests, signatures, method_ids))

            fallback_jumpdest = find_fallback_jumpdest(assembly, address_to_line)
            if fallback_jumpdest is not None:
                funcs_data.append((fallback_jumpdest, 'fallback()', None))

            funcs_data.sort(key=operator.itemgetter(0))

            # 3. make a dict contract_address -> [{signature, start}]
            funcs_dict[address] = obtain_funcs_dict(assembly, address_to_line, funcs_data)

        for i in range(1, len(contract_addresses)):
            for j in range(i):
                addresses = [contract_addresses[i], contract_addresses[j]]
                f_data = [funcs_dict[addresses[0]], funcs_dict[addresses[1]]]
                SimilarFinder(
                    f_data,
                    addresses,
                    self.no_operands,
                    self.diff_percentage,
                ).find_similar()
