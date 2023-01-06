from difflib import context_diff
from pyevmasm import Instruction



def is_same_by_diff(diff) -> bool:
    return len(diff) == 0


def is_significant_diff(diff, diff_percentage: int = 0) -> bool:
    #TODO: use diff_percentage
    return not is_same_by_diff(diff)


class SimilarFinder:
    def __init__(
        self,
        f_data,
        addresses,
        no_operands: bool = False,
        diff_percentage: int = 0
    ):
        self.functions_unwrapped_assembly = [
            [k['unwrapped_assembly'] for k in f_data[0]],
            [k['unwrapped_assembly'] for k in f_data[1]],
        ]

        self.signature = [
            [k['signature'] for k in f_data[0]],
            [k['signature'] for k in f_data[1]],
        ]

        self.address = addresses
        self.no_operands = no_operands
        self.diff_percentage = diff_percentage
    
    def find_similar(self) -> list[(str, str)]:
        similar = []
        used = set()

        for i0 in range(len(self.functions_unwrapped_assembly[0])):
            for i1 in range(len(self.functions_unwrapped_assembly[1])):
                diff = self._find_diff(i0, i1, self.no_operands)

                if (self.signature[0][i0], self.signature[1][i1]) in used:
                    continue

                if not is_significant_diff(diff, self.diff_percentage):
                    similar.append((self.signature[0][i0], self.signature[1][i1]))
                    used.add((self.signature[0][i0], self.signature[1][i1]))
                    print('Found similar functions in contracts:')
                    print(f"\t{self.address[0]}: {self.signature[0][i0]}")
                    print(f"\t{self.address[1]}: {self.signature[1][i1]}")
                    print()

                for m in range(2):
                    used.add((self.signature[0][i0], self.signature[1][i1]))

        return similar
    
    def _find_diff(self, id0: int, id1: int, no_operands: bool = False) -> list[str]:
        f0_operators = self._prepare_assembly(0, id0, no_operands)
        f1_operators = self._prepare_assembly(1, id1, no_operands)

        return list(context_diff(f0_operators, f1_operators))

    # id is 0 or 1
    def _prepare_assembly(self, id, i, no_operands: bool = False) -> str:
        if no_operands:
            return '\n'.join([str(line) for line in self.functions_unwrapped_assembly[id][i]])
        return self.functions_unwrapped_assembly[id][i]
