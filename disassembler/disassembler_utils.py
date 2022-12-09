from pyevmasm import disassemble_all, Instruction


def disassemble(bytecode, pc=0, add_address=False, hex_address=False) -> str:
    """Disassemble a bytecode string into a list of instructions.

    :param bytecode: bytecode string
    :param pc: start address
    :param add_address: add addresses to the instructions
    :param hex_address: use hex addresses
    :return: assembly code
    """
    instructions = disassemble_all(bytecode, pc=pc)
    formatter = _get_instruction_formatter(add_address, hex_address)
    return '\n'.join(map(formatter, instructions))


def _get_instruction_formatter(add_address: bool, hex_address: bool) -> callable:
    if not add_address:
        return _format_instruction_without_address
    elif hex_address:
        return _format_instruction_with_hex_address
    else:
        return _format_instruction_with_decimal_address


def _format_instruction_without_address(instruction: Instruction) -> str:
    return str(instruction)


def _format_instruction_with_hex_address(instruction: Instruction) -> str:
    return f'{instruction.pc:#6x} {instruction}'


def _format_instruction_with_decimal_address(instruction: Instruction) -> str:
    return f'{instruction.pc:6d} {instruction}'
