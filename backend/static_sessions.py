"""Hashed public build assets never read, refresh or vary by a login cookie."""
import re
from flask import request
from flask.sessions import SecureCookieSessionInterface
from .admin_host import is_admin_host

def public_asset(path):
    return bool(re.fullmatch(r'/assets/[^/]+-[A-Za-z0-9_-]{8,}\.(?:js|css|woff2?|ttf)',path))

class AssetSessionInterface(SecureCookieSessionInterface):
    def open_session(self,app,request):
        if public_asset(request.path):return self.session_class()
        loaded=super().open_session(app,request)
        if loaded is not None and app.config['ADMIN_SUBDOMAIN_ENABLED'] and app.config['ADMIN_REDIRECT_ENABLED'] and not is_admin_host(app, request):
            loaded.pop('uid', None)
        return loaded

    def save_session(self,app,session,response):
        if public_asset(request.path):return
        return super().save_session(app,session,response)

    def get_cookie_name(self, app):
        return '__Host-pyq-admin' if is_admin_host(app, request) else super().get_cookie_name(app)

    def get_cookie_domain(self, app):
        return None if is_admin_host(app, request) else super().get_cookie_domain(app)

    def get_cookie_path(self, app):
        return '/' if is_admin_host(app, request) else super().get_cookie_path(app)

    def get_cookie_secure(self, app):
        return is_admin_host(app, request) or super().get_cookie_secure(app)

    def get_signing_serializer(self, app):
        serializer = super().get_signing_serializer(app)
        if serializer is not None and is_admin_host(app, request):
            serializer.salt = b'pyq-admin-session-v1'
        return serializer
