"""Route the administration console through its own HTTPS origin."""

from flask import abort, redirect, request

ADMIN_HOST = 'admin.mauryahub.in'
ADMIN_ORIGIN = f'https://{ADMIN_HOST}'
ADMIN_PAGE_PATHS = {'/admin', '/admin/login', '/login'}


def is_admin_host(app, req):
    return app.config['ADMIN_SUBDOMAIN_ENABLED'] and req.host.lower() == ADMIN_HOST


def install(app):
    @app.before_request
    def route_admin_host():
        path = request.path.rstrip('/') or '/'
        safe_method = request.method in ('GET', 'HEAD')
        if is_admin_host(app, request):
            if path == '/' and safe_method:
                return redirect(ADMIN_ORIGIN + '/admin')
            return
        if not app.config['ADMIN_SUBDOMAIN_ENABLED'] or not app.config['ADMIN_REDIRECT_ENABLED']:
            return
        admin_page = path in ADMIN_PAGE_PATHS or (path == '/custom-exam' and not app.config['CUSTOM_EXAM_BETA_ENABLED'])
        if admin_page and safe_method:
            return redirect(ADMIN_ORIGIN + ('/admin/login' if path == '/login' else path))
        if path == '/api/admin' or path.startswith('/api/admin/') or path in ('/api/auth/login', '/api/auth/logout'):
            abort(404)

    @app.after_request
    def protect_admin_pages(response):
        on_admin_host = is_admin_host(app, request)
        if on_admin_host or response.location in {ADMIN_ORIGIN + path for path in (*ADMIN_PAGE_PATHS, '/custom-exam')}:
            response.headers['X-Robots-Tag'] = 'noindex, nofollow'
            if response.mimetype == 'text/html' or response.status_code in (302, 303, 307, 308):
                response.headers['Cache-Control'] = 'private, no-store'
        if on_admin_host:
            response.headers['Content-Security-Policy'] += "; frame-ancestors 'none'"
            response.headers['X-Frame-Options'] = 'DENY'
        return response
