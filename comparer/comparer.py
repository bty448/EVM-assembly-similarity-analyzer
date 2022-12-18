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

        for address in set(contract_addresses):
            # plan:

            abi = self.manager.get_abi(address)
            assembly = self.manager.get_assembly(address)
            assembly_dict[address] = assembly

            # 1. get all functions hash codes from abi
            signatures, method_ids = get_functions_info(abi)

            # 2. find occurrences in assembly file and find corresponding position of JUMPDEST in code
            functions_jumpdests = find_jumpdests_of_functions(assembly=assembly, method_ids=method_ids)
            funcs_data = list(zip(functions_jumpdests, signatures, method_ids))

            fallback_jumpdest = find_fallback_jumpdest(assembly=assembly)
            if fallback_jumpdest is not None:
                funcs_data.append((fallback_jumpdest, 'fallback()', None))

            funcs_data.sort(key=operator.itemgetter(0))

            # 3. split assembly by functions and obtain a dict
            # where by the address of the contract we get the list of functions
            funcs_dict[address] = split_assembly_on_funcs(
                assembly=assembly,
                funcs_data=funcs_data
            )

        for i in range(1, len(contract_addresses)):
            for j in range(i):
                addresses = [contract_addresses[i], contract_addresses[j]]
                funcs_with_signature = [funcs_dict[addresses[0]], funcs_dict[addresses[1]]]
                assemblies = [assembly_dict[addresses[0]], assembly_dict[addresses[1]]]
                SimilarFinder(
                    funcs_with_signature=funcs_with_signature,
                    addresses=addresses,
                    assemblies=assemblies,
                    no_operands=self.no_operands,
                    diff_percentage=self.diff_percentage,
                ).find_similar()
