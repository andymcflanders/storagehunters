"""SSRF protection for outbound webhook delivery.

Webhook URLs are attacker-influenced (any authenticated household member can
create one), so before the server makes an outbound request we refuse targets
that point back into the infrastructure.

Threat-model note: this is self-hosted software, and the *legitimate* common
case is a webhook aimed at a Home Assistant box on the same LAN (a private
RFC1918 address). So the default policy allows private LAN ranges but always
refuses loopback, link-local (which covers the 169.254.169.254 cloud-metadata
endpoint), multicast, and reserved space. Operators who want the stricter
posture can set `webhook_block_private_networks=true`.

Validation happens in two places:
- at create/update time, cheaply and without DNS, to give the user immediate
  feedback and to reject literal-IP targets; and
- at delivery time, with DNS resolution, which is the real defense — it is the
  only check that resists DNS-rebinding between creation and delivery.
"""

import ipaddress
import socket
from urllib.parse import urlparse

from app.config import get_settings


class WebhookURLError(ValueError):
    """Raised when a webhook URL is not an allowed delivery target."""


def _blocked_reason(ip: ipaddress.IPv4Address | ipaddress.IPv6Address, *, block_private: bool) -> str | None:
    """Return a human reason if this IP is off-limits, else None."""
    # Unwrap IPv4-mapped IPv6 (e.g. ::ffff:127.0.0.1) so the checks below see
    # the real v4 address rather than a "global" v6 wrapper.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped

    if ip.is_unspecified:
        return "unspecified address"
    if ip.is_loopback:
        return "loopback address"
    if ip.is_link_local:
        return "link-local / metadata address"
    if ip.is_multicast:
        return "multicast address"
    if ip.is_reserved:
        return "reserved address"
    if block_private and ip.is_private:
        return "private network address"
    return None


def validate_webhook_url(url: str, *, resolve: bool = False) -> None:
    """Validate a webhook target URL.

    Raises WebhookURLError if the URL is malformed or points at a disallowed
    target. With resolve=True the hostname is resolved and every returned
    address is checked (use this at delivery time). With resolve=False only
    the scheme and any literal-IP host are checked (use this at create/update
    time — it never does DNS, so it's fast and CI-friendly).
    """
    settings = get_settings()
    if not settings.webhook_ssrf_protection:
        return

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise WebhookURLError("Webhook URL must use http or https")

    host = parsed.hostname
    if not host:
        raise WebhookURLError("Webhook URL must include a host")

    block_private = settings.webhook_block_private_networks

    # Literal IP target — check it directly regardless of `resolve`.
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        reason = _blocked_reason(ip, block_private=block_private)
        if reason:
            raise WebhookURLError(f"Webhook URL host is a {reason}")
        return

    if not resolve:
        return

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise WebhookURLError(f"Webhook URL host could not be resolved: {exc}")

    for info in infos:
        addr = info[4][0]
        try:
            resolved = ipaddress.ip_address(addr)
        except ValueError:
            continue
        reason = _blocked_reason(resolved, block_private=block_private)
        if reason:
            raise WebhookURLError(f"Webhook URL resolves to a {reason} ({addr})")
