"""Rate-limit identity that a client cannot rotate by editing headers or cookies.

Previously the limiter key was the browser's own session cookie, falling back
to the *first* X-Forwarded-For entry. Both are chosen by the client: dropping
the cookie and sending a random X-Forwarded-For gave a fresh limit on every
request (admin-login brute force, feedback/contact spam).

Resolution order (pure string/ipaddress work, no I/O):
1. CF-Connecting-IP, written by Cloudflare at its edge (Render and a proxied
   custom domain both sit behind Cloudflare). Can be disabled with
   TRUST_CF_CONNECTING_IP=false if the app is ever reached without Cloudflare.
2. X-Forwarded-For read from the RIGHT: proxies append the address that
   connected to them, so the right-most public address is the one our own
   proxy chain saw. Spoofed entries a client adds are further left and ignored.
   Private/internal proxy hops are skipped so users never share one bucket.
3. The socket peer address.
"""
import ipaddress
import os

from flask import request, session


def _public_ip(value):
    try:
        ip = ipaddress.ip_address(value.strip())
    except ValueError:
        return None
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified or ip.is_multicast:
        return None
    return str(ip)


def client_ip():
    if os.getenv('TRUST_CF_CONNECTING_IP', 'true').lower() != 'false':
        cf = request.headers.get('CF-Connecting-IP', '')
        if cf:
            ip = _public_ip(cf)
            if ip:
                return ip
    forwarded = request.headers.get('X-Forwarded-For', '')
    for part in reversed(forwarded.split(',')[-10:]):
        ip = _public_ip(part)
        if ip:
            return ip
    return request.remote_addr or 'unknown'


def ip_key():
    """Per network address: used for login and per-IP abuse caps."""
    return 'ip:' + client_ip()


def visitor_key():
    """Per browser when a session exists, so students sharing a campus/mobile
    IP do not exhaust each other's quota. Always pair it with an ip_key limit,
    because a client can discard its cookie."""
    try:
        visitor = session.get('visitor')
    except Exception:
        visitor = None
    return 'visitor:' + str(visitor)[:32] if visitor else ip_key()
