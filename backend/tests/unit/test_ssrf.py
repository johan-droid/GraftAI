from backend.utils.ssrf import is_safe_url


def test_safe_urls():
    assert is_safe_url("https://google.com")
    assert is_safe_url("http://example.com")
    assert is_safe_url("https://api.github.com/v3")

def test_unsafe_urls():
    assert not is_safe_url("http://localhost:8000")
    assert not is_safe_url("http://127.0.0.1")
    assert not is_safe_url("http://192.168.1.1")
    assert not is_safe_url("http://10.0.0.1")
    assert not is_safe_url("http://169.254.169.254")
    assert not is_safe_url("file:///etc/passwd")
    assert not is_safe_url("ftp://example.com")

def test_invalid_urls():
    assert not is_safe_url("not a url")
    assert not is_safe_url("")
    assert not is_safe_url(None)
