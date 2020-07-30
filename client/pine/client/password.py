# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import base64
import bcrypt
import hashlib

def hash_password(password: str) -> str:
    """Hashes the given password for use in user object.
    
    :param password: password
    :type password: str
    
    :returns: hashed password
    :rtype: str
    """
    sha256 = hashlib.sha256(password.encode()).digest().replace(b"\x00", b"")
    hashed_password_bytes = bcrypt.hashpw(sha256, bcrypt.gensalt())
    return base64.b64encode(hashed_password_bytes).decode()

def check_password(password: str, hashed_password: str) -> str:
    """Checks the given password against the given hash.
    
    :param password: password to check
    :type password: str
    :param hashed_password: hashed password to check against
    :type hashed_password: str
    
    :returns: whether the password matches the hash
    :rtype: bool
    """
    sha256 = hashlib.sha256(password.encode()).digest().replace(b"\x00", b"")
    hashed_password_bytes = base64.b64decode(hashed_password.encode())
    return bcrypt.checkpw(sha256, hashed_password_bytes)
