from difflib import context_diff


def is_same_by_diff(diff) -> bool:
    return len(diff) == 0


def is_significant_diff(diff, diff_percentage: int = 0) -> bool:
    # TODO ignore arguments only in jumps (check recursively)
    return not is_same_by_diff(diff)


def find_diff(funcs: (dict, dict), no_operands: bool = False) -> list[str]:
    f1_assembly = funcs[0]['function_assembly']
    f2_assembly = funcs[1]['function_assembly']

    f1_operators = prepare_assembly(f1_assembly, no_operands=no_operands)
    f2_operators = prepare_assembly(f2_assembly, no_operands=no_operands)

    return list(context_diff(f1_operators, f2_operators))


def prepare_assembly(func_assembly: str, no_operands: bool = False) -> str:
    if no_operands:
        return '\n'.join([line.split()[0] for line in func_assembly.splitlines()])
    return func_assembly
