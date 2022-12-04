from pyevmasm import disassemble_all


def disassemble(bytecode, pc=0, add_addresses=False):
    """Disassemble a bytecode string into a list of instructions.

    :param bytecode: bytecode string
    :param pc: start address
    :param add_addresses: add addresses to the instructions
    :return: list of instructions
    """
    assembler = ""
    for instruction in disassemble_all(bytecode, pc=pc):
        if add_addresses:
            assembler += f"{instruction.pc:08d} {instruction}\n"
        else:
            assembler += f"{instruction}\n"
    return assembler
