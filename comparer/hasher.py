from Crypto.Hash import keccak


class Hasher:
    def __init__(self, bits=256):
        self.bits = bits

    def get_hash(self, data: str) -> str:
        """
        Calculates hash from the data
        :param data: data to hash
        :return: hash of the data
        """
        return keccak.new(digest_bits=self.bits, data=data.encode('utf-8')).hexdigest()

    def get_method_id(self, signature: str) -> str:
        """
        Calculates method id from the signature
        :param signature: method signature
        :return: method id
        """
        return self.get_hash(signature)[:8]
