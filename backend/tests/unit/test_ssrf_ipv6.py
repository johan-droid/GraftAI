from backend.utils.ssrf import is_safe_url


def test_unsafe_ipv6_urls():
    assert not is_safe_url("http://[::1]")
    assert not is_safe_url("http://[fc00::1]")
