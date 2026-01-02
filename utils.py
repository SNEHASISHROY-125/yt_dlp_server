# utils.py
import uuid

def new_token():
    return uuid.uuid4().hex

import hashlib

def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()
