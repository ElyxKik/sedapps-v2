import bcrypt

_MAX = 72  # bcrypt hard limit (bytes)


def _truncate(plain: str) -> bytes:
    return plain.encode("utf-8")[:_MAX]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_truncate(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
