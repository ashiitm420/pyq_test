PUBLIC = 'https://www.mauryahub.in'
ADMIN = 'https://admin.mauryahub.in'


def sign_in(client, origin):
    csrf = client.get('/api/session', base_url=origin).json['csrf']
    return client.post(
        '/api/auth/login',
        base_url=origin,
        json={'email': 'admin@example.test', 'password': 'test-password-123'},
        headers={'X-CSRF-Token': csrf},
    )


def test_admin_host_supports_testing_before_redirect(app, client):
    app.config['ADMIN_SUBDOMAIN_ENABLED'] = True
    assert client.get('/', base_url=ADMIN).location == ADMIN + '/admin'
    assert client.get('/admin', base_url=PUBLIC).status_code == 200

    response = sign_in(client, ADMIN)
    assert response.json['user']['role'] == 'ADMIN'
    cookie = response.headers['Set-Cookie']
    assert cookie.startswith('__Host-pyq-admin=')
    assert all(flag in cookie for flag in ('Secure', 'HttpOnly', 'Path=/', 'SameSite=Lax'))
    assert 'Domain=' not in cookie
    assert client.get('/api/admin/stats', base_url=ADMIN).status_code == 200
    assert client.get('/api/session', base_url=PUBLIC).json['user'] is None

    shell = client.get('/admin', base_url=ADMIN)
    assert shell.status_code == 200
    assert 'no-store' in shell.headers['Cache-Control']
    assert "frame-ancestors 'none'" in shell.headers['Content-Security-Policy']
    assert 'workers.dev' not in shell.headers['Content-Security-Policy']


def test_cutover_redirects_admin_and_rejects_legacy_public_sessions(app, client):
    assert sign_in(client, PUBLIC).status_code == 200
    cookie = client.get_cookie('session', domain='www.mauryahub.in')
    assert cookie is not None
    app.config.update(ADMIN_SUBDOMAIN_ENABLED=True, ADMIN_REDIRECT_ENABLED=True)

    for path, new_path in [('/admin', '/admin'), ('/admin/login', '/admin/login'), ('/login', '/admin/login')]:
        response = client.get(path, base_url=PUBLIC)
        assert response.status_code == 302
        assert response.location == ADMIN + new_path
        assert 'no-store' in response.headers['Cache-Control']
    assert client.get('/api/session', base_url=PUBLIC).json['user'] is None
    assert sign_in(client, PUBLIC).status_code == 404
    response = client.get('/api/admin/stats', base_url=PUBLIC, headers={'X-Forwarded-Host': 'admin.mauryahub.in'})
    assert response.status_code == 404
    assert client.get('/api/admin/google-drive/callback', base_url=PUBLIC).status_code == 404

    client.set_cookie('__Host-pyq-admin', cookie.value, domain='admin.mauryahub.in')
    assert client.get('/api/session', base_url=ADMIN).json['user'] is None
    assert client.get('/api/admin/stats', base_url=ADMIN).status_code == 401

    assert client.get('/', base_url=PUBLIC).status_code == 200
    assert client.get('/api/home', base_url=PUBLIC).status_code == 200


def test_public_custom_exam_stays_on_public_origin_after_admin_cutover(app, client):
    app.config.update(ADMIN_SUBDOMAIN_ENABLED=True, ADMIN_REDIRECT_ENABLED=True)
    assert client.get('/custom-exam', base_url=PUBLIC).location == ADMIN + '/custom-exam'
    app.config['CUSTOM_EXAM_BETA_ENABLED'] = True
    response = client.get('/custom-exam', base_url=PUBLIC)
    assert response.status_code == 200
    assert 'noindex' in response.headers['X-Robots-Tag']
