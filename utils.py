import base64
from hashlib import md5


def basic_auth(username: str, password: str) -> str:
    """
    Creates a Basic Authentication header value
    from the given username and password.

    :param username: The username.
    :param password: The password.
    :return: A Base64-encoded string containing the credentials.
    """
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return encoded_credentials


def get_sign(data: dict) -> str:
    """
    Generates a signature for the given data dictionary
    using a salt and MD5 hashing.

    :param data: A dictionary containing the data to sign.
    :return: An MD5 hash string representing the signature.
    """
    from config import SALT

    elements = [md5(str(i).encode()).hexdigest() for i in data.values()]
    elements.sort()
    return md5((SALT + ''.join(elements)).encode()).hexdigest()
