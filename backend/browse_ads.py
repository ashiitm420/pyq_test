"""CSP and route scope for the publisher's 320 × 50 JS Async banner."""

import re

KEY = '04b45b8b141ae47be2afd0bd9dac1a47'
SCRIPT = f'https://bauval.org/22/{KEY}'
BROWSE_ROUTE = re.compile(r'(?:|(?:course|paper)/[0-9]+|exam/[^/]+)')


def content_security_policy(policy):
    return (policy
            .replace("script-src 'self'", f"script-src 'self' {SCRIPT}")
            .replace("frame-src 'self'", "frame-src 'self' https://bauval.org https://mamshirt.com")
            .replace("connect-src 'self'", "connect-src 'self' https://bauval.org https://mamshirt.com https://aqml.org https://static.nresystems.com")
            .replace("img-src 'self'", "img-src 'self' https://bauval.org https://mamshirt.com https://aqml.org"))
