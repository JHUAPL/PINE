# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import base64
import bcrypt
import hashlib

def hash_password(password: str) -> str:
    sha256 = hashlib.sha256(password.encode()).digest()
    hashed_password_bytes = bcrypt.hashpw(sha256, bcrypt.gensalt())
    return base64.b64encode(hashed_password_bytes).decode()

def check_password(password: str, hashed_password: str):
    sha256 = hashlib.sha256(password.encode()).digest()
    hashed_password_bytes = base64.b64decode(hashed_password.encode())
    return bcrypt.checkpw(sha256, hashed_password_bytes)
