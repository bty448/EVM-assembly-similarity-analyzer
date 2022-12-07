from Crypto.Hash import keccak


def get_hash(data: str) -> str:
    """
    Calculates hash from the data
    :param data: data to hash
    :return: hash of the data
    """
    return keccak.new(digest_bits=256, data=data.encode('ascii')).hexdigest()


def get_method_id(signature: str) -> str:
    """
    Calculates method id from the signature
    :param signature: method signature
    :return: method id
    """
    return get_hash(signature)[:8]
