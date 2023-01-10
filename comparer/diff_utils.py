from difflib import context_diff
from pyevmasm import Instruction


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
    
    def is_significant_diff(self, diff) -> bool:
        (len_diff, len1, len2) = diff
        percentage = len_diff / max(len1, len2) * 100.0
        return percentage > self.diff_percentage

    def find_similar(self) -> list[(str, str)]:
        similar = []
        used = set()

        for i0 in range(len(self.functions_unwrapped_assembly[0])):
            for i1 in range(len(self.functions_unwrapped_assembly[1])):
                if (self.signature[0][i0], self.signature[1][i1]) in used:
                    continue

                if not self.is_significant_diff(self._find_diff(i0, i1, self.no_operands)):
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

        diff = list(context_diff(f0_operators, f1_operators))

        return (len(diff), len(f0_operators), len(f1_operators))

    # id is 0 or 1
    def _prepare_assembly(self, id, i, no_operands: bool = False) -> str:
        if no_operands:
            return '\n'.join([str(line) for line in self.functions_unwrapped_assembly[id][i]])
        return self.functions_unwrapped_assembly[id][i]
