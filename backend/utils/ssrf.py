import ipaddress
import socket
from urllib.parse import urlparse


def is_safe_url(url: str) -> bool:
    """
    Validates if a URL is safe to make outbound requests to.
    Prevents SSRF by blocking loopback, private, and reserved IP addresses.
    """
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        if not hostname:
            return False
        if parsed_url.scheme not in ("http", "https"):
            return False
        try:
            addr_info = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            return False
        for info in addr_info:
            ip_str = info[4][0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_loopback or ip.is_private or ip.is_reserved or ip.is_multicast or ip.is_unspecified or ip.is_link_local:
                return False
        return True
    except Exception:
        return False
