from difflib import context_diff
from pyevmasm import Instruction


def is_same_by_diff(diff) -> bool:
    return len(diff) == 0


def is_significant_diff(diff, diff_percentage: int = 0) -> bool:
    # TODO ignore arguments only in jumps (check recursively)
    return not is_same_by_diff(diff)


class SimilarFinder:
    def __init__(
        self,
        funcs_with_signature,
        addresses,
        assemblies,
        no_operands: bool = False,
        diff_percentage: int = 0
    ):
        self.assembly = assemblies

        # 'function_bounds' is {'start': int, 'finish': int}
        self.func_data = [
            [k['function_bounds'] for k in funcs_with_signature[0]],
            [k['function_bounds'] for k in funcs_with_signature[0]],
        ]

        self.signature = [
            [k['signature'] for k in funcs_with_signature[0]],
            [k['signature'] for k in funcs_with_signature[1]],
        ]

        self.address = addresses
        self.no_operands = no_operands
        self.diff_percentage = diff_percentage
    
    def find_similar(self) -> list[(str, str)]:
        similar = []
        used = set()

        for i0, f0_data in enumerate(self.func_data[0]):
            for i1, f1_data in enumerate(self.func_data[1]):
                diff = self._find_diff(f0_data, f1_data, self.no_operands)

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
    
    def _find_diff(self, f0_data: dict, f1_data: dict, no_operands: bool = False) -> list[str]:
        f0_operators = self._prepare_assembly(0, f0_data, no_operands=no_operands)
        f1_operators = self._prepare_assembly(1, f1_data, no_operands=no_operands)

        return list(context_diff(f0_operators, f1_operators))

    # id is 0 or 1
    def _prepare_assembly(self, id: int, f_data: dict, no_operands: bool = False) -> str:
        func_assembly = self._unwrap_recursion(self.assembly[id], f_data['start'], f_data['finish'])

        if no_operands:
            return '\n'.join([str(line) for line in func_assembly])
        return func_assembly

    def _unwrap_recursion(self, assembly: list[Instruction], start: int, finish: int, visited: set = None):
        address_to_line = {instruction.pc: i for i, instruction in enumerate(assembly)}

        unwrapped = []
        if visited is None:
            visited = set()

        for i in range(start, finish + 1):
            if i in visited:
                continue
            instruction = assembly[i]
            visited.add(i)
            unwrapped.append(instruction)
            if instruction.name == 'JUMP' or instruction.name == 'JUMPI':
                if assembly[i - 1].name[:4] == 'PUSH':
                    address = assembly[i - 1].operand
                    if address in address_to_line:
                        line = address_to_line[address]
                        if assembly[line].name == 'JUMPDEST':
                            rec_start = line + 1
                            if rec_start not in visited:
                                unwrapped += self._unwrap_recursion(assembly=assembly, start=rec_start, finish=finish, visited=visited)

        return unwrapped
