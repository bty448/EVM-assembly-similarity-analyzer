from pyevmasm import Instruction
from .hash_utils import get_method_id


HALTING_INSTRUCTIONS = set(['RETURN', 'REVERT', 'STOP', 'SELFDESTRUCT', 'ABORT', 'INVALID', 'CALL', 'DELEGATECALL', 'STATICCALL'])

def get_functions_info(abi: list) -> (list[str], list[int]):
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


def find_fallback_jumpdest(assembly: list[Instruction], address_to_line: dict):
    comparison_ops = set(['EQ', 'LT', 'GT'])

    for i, instruction in enumerate(assembly):
        if instruction.name != 'PUSH4':
            continue
        if i + 3 >= len(assembly):
            # no jump
            continue
        if assembly[i + 1].name not in comparison_ops:
            # not a header pattern
            continue
        expected_jump = assembly[i + 3]
        if expected_jump.name != 'JUMP' and expected_jump.name != 'JUMPI':
            # no jump
            continue
        if assembly[i + 2].name[:4] != 'PUSH':
            # no push
            continue
        if i + 5 >= len(assembly):
            # no fallback
            continue
        if assembly[i + 5].name != 'JUMP':
            # no fallback
            continue
        fallback_dest = assembly[i + 4]
        if fallback_dest.name[:4] != 'PUSH':
            # no fallback
            continue
        fallback_dest_address = fallback_dest.operand
        if fallback_dest_address not in address_to_line:
            # no such address
            continue
        return fallback_dest_address

    return None


def find_jumpdests_of_functions(assembly: list[Instruction], address_to_line: dict, method_ids: list[int]) -> list[int]:
    # Header pattern:
    # PUSH4 method_id
    # EQ | LT | GT
    # PUSH2 method_address
    # JUMPI
    # PUSH2 fallback_address
    # JUMP
    jumpdests = []

    comparison_ops = set(['EQ', 'LT', 'GT'])

    for method_id in method_ids:
        for i, instruction in enumerate(assembly):
            if instruction.name != 'PUSH4' or instruction.operand != method_id:
                continue
            if i + 3 >= len(assembly):
                # no jump
                continue
            if assembly[i + 1].name not in comparison_ops:
                # not a header pattern
                continue
            expected_jump = assembly[i + 3]
            if expected_jump.name != 'JUMP' and expected_jump.name != 'JUMPI':
                # no jump
                continue
            push_address = assembly[i + 2]
            if push_address.name[:4] != 'PUSH':
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

def unwrap_recursion(assembly: list[Instruction], address_to_line: dict, start: int) -> list[Instruction]:
        unwrapped = []
        visited = set()

        rec_stack = []

        i = start
        while True:
            if i >= len(assembly):
                print('reached end')
                return unwrapped

            if i in visited:
                i += 1
                continue

            instruction = assembly[i]
            visited.add(i)
            unwrapped.append(instruction)

            if instruction.name in HALTING_INSTRUCTIONS:
                if len(rec_stack) == 0:
                    print(instruction.name)
                    return unwrapped
                i = rec_stack.pop()
                continue

            if instruction.name == 'JUMP' or instruction.name == 'JUMPI':
                if assembly[i - 1].name[:4] == 'PUSH':
                    address = assembly[i - 1].operand
                    if address in address_to_line:
                        line = address_to_line[address]
                        if assembly[line].name == 'JUMPDEST':
                            if (line + 1) not in visited:
                                if instruction.name == 'JUMPI' and (i + 1) not in visited:
                                    rec_stack.append(i + 1)
                                i = line + 1
                                continue
                        else:
                            print('bad jump')
            i += 1

def obtain_funcs_dict(assembly, address_to_line, funcs_data: list[(int, str, str)]) -> list[dict]:
        funcs = []

        for i in range(len(funcs_data)):
            (jumpdest, signature, _) = funcs_data[i - 1]
            if jumpdest == -1:
                continue
            funcs.append({
                'signature': signature,
                'unwrapped_assembly': unwrap_recursion(assembly, address_to_line, jumpdest + 1),
            })

        return funcs
