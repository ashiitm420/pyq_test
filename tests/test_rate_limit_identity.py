"""Rate limits must not reset when a client drops its cookie or forges X-Forwarded-For."""
import pytest
from backend.models import db


@pytest.fixture
def limited_app(tmp_path):
    from backend import create_app, limiter
    app = create_app({'TESTING': True, 'STORAGE_BACKEND': 'local', 'UPLOAD_DIR': str(tmp_path/'uploads'),
                      'SQLALCHEMY_DATABASE_URI': 'sqlite:///'+str(tmp_path/'rate.db'), 'RATELIMIT_ENABLED': True})
    with app.app_context():
        db.create_all()
        limiter.reset()
        try:
            yield app
        finally:
            db.session.remove()
            db.drop_all()
            limiter.reset()


def fresh_login(app, n, real_ip='49.36.10.20'):
    # A brand-new client every time (no cookie) with a forged first XFF entry;
    # Render's proxy appends the real address on the right.
    with app.test_client() as client:
        headers = {'X-Forwarded-For': f'203.0.113.{n}, {real_ip}'}
        csrf = client.get('/api/session', headers=headers).get_json()['csrf']
        return client.post('/api/auth/login', json={'email': 'x@example.com', 'password': 'wrong'},
                           headers={**headers, 'X-CSRF-Token': csrf}).status_code


def test_login_limit_survives_cookie_reset_and_forged_forwarded_for(limited_app):
    codes = [fresh_login(limited_app, n) for n in range(11)]
    assert codes[:10] == [401]*10
    assert codes[10] == 429
    # A different real address still has its own allowance.
    assert fresh_login(limited_app, 99, real_ip='49.36.10.21') == 401


def test_feedback_ip_cap_survives_cookie_reset(limited_app):
    codes = []
    for n in range(21):
        with limited_app.test_client() as client:
            headers = {'X-Forwarded-For': f'198.51.100.{n}, 49.36.10.30'}
            csrf = client.get('/api/session', headers=headers).get_json()['csrf']
            codes.append(client.post('/api/feedback', json={'stars': 5, 'message': 'Helpful site'},
                                     headers={**headers, 'X-CSRF-Token': csrf}).status_code)
    assert codes[:20] == [201]*20
    assert codes[20] == 429


def test_feedback_post_keeps_paper_cache(limited_app):
    from backend import content_cache
    calls = []
    with limited_app.test_request_context('/'):
        content_cache.cached('all-visible-papers', lambda: calls.append(1) or ['rows'])
    with limited_app.test_client() as client:
        csrf = client.get('/api/session').get_json()['csrf']
        assert client.post('/api/feedback', json={'stars': 4, 'message': 'Nice'},
                           headers={'X-CSRF-Token': csrf}).status_code == 201
    with limited_app.test_request_context('/'):
        assert content_cache.cached('all-visible-papers', lambda: calls.append(1) or ['rows']) == ['rows']
    assert calls == [1]
