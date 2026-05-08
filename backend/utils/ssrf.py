import urllib.parse
import ipaddress
import socket

def is_safe_url(url: str) -> bool:
    """
    Validates if a URL is safe to make an outbound request to.
    Prevents SSRF by blocking requests to internal IP addresses and localhost.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Resolve hostname to IP to catch DNS rebinding/localhost tricks
        try:
            ip_addresses = socket.gethostbyname_ex(hostname)[2]
        except socket.gaierror:
            return False

        for ip_str in ip_addresses:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                return False

        return True
    except Exception:
        return False
