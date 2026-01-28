import hashlib

def hash_mobile(mobile_no: str) -> str:
    return hashlib.sha256(mobile_no.encode()).hexdigest()

def mask_mobile(mobile_no: str) -> str:
    return mobile_no[:2] + "******" + mobile_no[-2:]
