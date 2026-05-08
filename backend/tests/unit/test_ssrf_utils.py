import pytest
from backend.utils.ssrf import is_safe_url

def test_ssrf_utils():
    assert is_safe_url("http://google.com") == True
    assert is_safe_url("https://example.com") == True
    assert is_safe_url("http://127.0.0.1") == False
    assert is_safe_url("http://localhost") == False
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") == False
    assert is_safe_url("file:///etc/passwd") == False
