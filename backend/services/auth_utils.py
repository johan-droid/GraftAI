from passlib.context import CryptContext

# Use bcrypt_sha256 first to avoid bcrypt's 72-byte limitation while still supporting existing bcrypt hashes.
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    # bcrypt only handles 72 bytes; bcrypt_sha256 pre-hashes and avoids this limit.
    b = password.encode("utf-8")
    if len(b) > 4096:
        raise ValueError("Password is too long")

    return pwd_context.hash(password)
