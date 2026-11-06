"""Hashed public build assets never read, refresh or vary by a login cookie."""
import re
from flask.sessions import SecureCookieSessionInterface

def public_asset(path):
    return bool(re.fullmatch(r'/assets/[^/]+-[A-Za-z0-9_-]{8,}\.(?:js|css|woff2?|ttf)',path))

class AssetSessionInterface(SecureCookieSessionInterface):
    def open_session(self,app,request):
        if public_asset(request.path):return self.session_class()
        return super().open_session(app,request)

    def save_session(self,app,session,response):
        from flask import request
        if public_asset(request.path):return
        return super().save_session(app,session,response)
