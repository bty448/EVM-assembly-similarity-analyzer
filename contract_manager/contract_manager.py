import json

from pyevmasm import disassemble_all, Instruction

from utils.file_utils import read_text, read_binary
from contract_manager.downloader import ContractDownloader


# TODO: add memory cache
class ContractManager:
    def __init__(self, downloader: ContractDownloader):
        self.downloader = downloader

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.downloader.__exit__(exc_type, exc_val, exc_tb)

    def get_abi(self, address: str) -> list:
        abi_str = self.try_do_action(action=self._read_abi, address=address)
        return json.loads(abi_str)

    def get_assembly(self, address: str) -> list[Instruction]:
        bytecode = self.get_bytecode(address=address)
        return list(disassemble_all(bytecode=bytecode))

    def get_bytecode(self, address: str) -> bytes:
        return self.try_do_action(action=self._read_bytecode, address=address)

    def try_do_action(self, action: callable, address: str):
        try:
            return action(address=address)
        except FileNotFoundError:
            self.downloader.download(address=address)
            return action(address=address)

    def _read_abi(self, address: str) -> str:
        return read_text(self.downloader.get_abi_path(address))

    def _read_bytecode(self, address: str) -> bytes:
        return read_binary(self.downloader.get_bytecode_path(address))
