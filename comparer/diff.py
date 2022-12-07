from difflib import context_diff


def is_same_by_diff(diff) -> bool:
    return len(diff) == 0


def is_significant_diff(diff) -> bool:
    # TODO ignore arguments only in jumps (check recursively)
    return not is_same_by_diff(diff)


def find_diff(funcs: (dict, dict)) -> list[str]:
    f1_assembly = funcs[0]['function_assembly']
    f2_assembly = funcs[1]['function_assembly']

    f1_operators = remove_args(f1_assembly)
    f2_operators = remove_args(f2_assembly)

    return list(context_diff(f1_operators, f2_operators))


def remove_args(func_assembly: str) -> str:
    return '\n'.join([line.split()[1] for line in func_assembly])
