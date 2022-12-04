from Crypto.Hash import keccak

class Hasher:
    def __init__(self, bits=256):
        self.bits = bits
        self._reset_hasher()
    
    def _reset_hasher(self):
        self.hasher = keccak.new(digest_bits=self.bits)
    
    def get_hash(self, str_to_hash: str):
        res = self.hasher.update(str_to_hash.encode('ascii'))
        self._reset_hasher()
        return res
