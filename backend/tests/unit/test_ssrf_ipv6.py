from backend.utils.ssrf import is_safe_url

def test_unsafe_ipv6_urls():
    assert is_safe_url("http://[::1]") == False
    assert is_safe_url("http://[fc00::1]") == False
