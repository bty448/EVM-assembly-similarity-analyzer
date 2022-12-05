from difflib import context_diff

def is_same_by_diff(diff):
    return len(diff) == 0

def is_significant_diff(diff):
    #TODO check with recursion
    return not is_same_by_diff(diff)

def find_diff(funcs):
    f1_assembly = funcs[0]['function_assembly']
    f2_assembly = funcs[1]['function_assembly']

    f1_operators = remove_args(f1_assembly)
    f2_operators = remove_args(f2_assembly)

    return context_diff(f1_operators, f2_operators)

def remove_args(func_assembly):
    for line in func_assembly:
        line = line.split(' ')[1]  # [0] is a number of the line and [2:] are arguments if any
