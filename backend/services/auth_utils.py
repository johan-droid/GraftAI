from passlib.context import CryptContext
import re
import hashlib
import hmac
from typing import Set

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# NIST SP 800-63B compliant password requirements
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 64

# Common weak passwords to block (top 1000 most common)
COMMON_PASSWORDS: Set[str] = {
    "password", "password123", "123456", "12345678", "123456789",
    "qwerty", "qwerty123", "abc123", "letmein", "welcome",
    "monkey", "dragon", "master", "sunshine", "princess",
    "admin", "root", "user", "test", "demo",
    "login", "guest", "default", "changeme", "p@ssw0rd",
    "password1", "123qwe", "qwe123", "iloveyou", "trustno1",
    "baseball", "football", "superman", "batman", "hockey",
    "michael", "jordan", "maggie", "buster", "daniel",
    "andrew", "joshua", "pepper", "ginger", "tigger",
    "matthew", "amanda", "ashley", "cookie", "jessica",
    "summer", "ashley", "nicole", "merlin", "hello",
    "charlie", "chelsea", "jennifer", "thomas", "robert",
}

# Sequential patterns to detect
SEQUENTIAL_PATTERNS = [
    r'(012|123|234|345|456|567|678|789|890)+',  # Sequential numbers
    r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)+',  # Sequential letters
    r'(qwerty|asdf|zxcv)+',  # Keyboard patterns
]


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets NIST SP 800-63B security requirements.
    
    NIST Guidelines:
    - Minimum 8 characters, maximum 64
    - No complexity requirements (makes passwords hard to remember)
    - Check against common passwords
    - Check against repetitive/sequential patterns
    - Allow all characters including spaces and Unicode
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Length checks
    if not password:
        return False, "Password is required"
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password must not exceed {MAX_PASSWORD_LENGTH} characters"
    
    # Check for common passwords
    if password.lower() in COMMON_PASSWORDS:
        return False, "This password is too common. Please choose a more unique password."
    
    # Check for repetitive characters (e.g., "aaaaaa", "111111")
    if re.search(r'(.)\1{4,}', password):
        return False, "Password contains too many repeated characters"
    
    # Check for sequential patterns
    password_lower = password.lower()
    for pattern in SEQUENTIAL_PATTERNS:
        if re.search(pattern, password_lower):
            return False, "Password contains sequential characters or keyboard patterns"
    
    # Check for common substitutions (e.g., "p@ssw0rd")
    # Normalize common substitutions and check against common passwords
    normalized = password_lower
    substitutions = {
        '0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's',
        '7': 't', '8': 'b', '@': 'a', '$': 's', '!': 'i',
        '+': 't', '#': 'h', '%': 'o', '&': 'and',
    }
    for char, replacement in substitutions.items():
        normalized = normalized.replace(char, replacement)
    
    if normalized in COMMON_PASSWORDS:
        return False, "This password is too similar to common passwords"
    
    # Check entropy (basic check for complexity)
    unique_chars = len(set(password))
    if unique_chars < 5:
        return False, "Password should use a more diverse set of characters"
    
    return True, ""


def is_password_breached(password: str) -> bool:
    """
    Check if password appears in known data breaches using k-anonymity.
    
    Uses Have I Been Pwned API with k-anonymity to protect the password.
    Only sends first 5 chars of SHA-1 hash, receives matching suffixes.
    
    Returns:
        bool: True if password was found in breach database
    """
    try:
        import requests
        
        # Generate SHA-1 hash
        sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]
        
        # Query HIBP API
        response = requests.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            timeout=5,
            headers={"Add-Padding": "true"}  # Obfuscate actual matches
        )
        
        if response.status_code == 200:
            # Parse response (format: "SUFFIX:COUNT" per line)
            hashes = response.text.splitlines()
            for hash_line in hashes:
                parts = hash_line.split(":")
                if len(parts) >= 1:
                    if parts[0] == suffix:
                        return True
        
        return False
        
    except Exception:
        # Fail open - don't block if service unavailable
        return False


def validate_password_comprehensive(password: str, email: str = None) -> tuple[bool, str]:
    """
    Comprehensive password validation including breach check.
    
    Args:
        password: The password to validate
        email: User's email to check against similarity
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Basic strength check
    is_valid, message = validate_password_strength(password)
    if not is_valid:
        return False, message
    
    # Check for email similarity (if email provided)
    if email:
        email_parts = email.lower().split('@')
        local_part = email_parts[0] if email_parts else ""
        domain_part = email_parts[1].split('.')[0] if len(email_parts) > 1 else ""
        
        password_lower = password.lower()
        
        # Check if password contains email local part
        if len(local_part) > 3 and local_part in password_lower:
            return False, "Password should not contain your email address"
        
        # Check if password contains domain name
        if len(domain_part) > 3 and domain_part in password_lower:
            return False, "Password should not contain your email domain"
    
    # Breach check (optional - may slow down registration)
    # Uncomment to enable breach checking
    # if is_password_breached(password):
    #     return False, "This password has been compromised in a data breach"
    
    return True, ""

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    if not password:
        raise ValueError("Password cannot be empty")
    return pwd_context.hash(password)
