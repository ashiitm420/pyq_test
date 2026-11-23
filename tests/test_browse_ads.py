import pytest

from backend.browse_ads import OPTIONS_HASH, SCRIPT

PUBLIC = 'https://www.mauryahub.in'
ADMIN = 'https://admin.mauryahub.in'


def test_browse_ads_require_admin_origin_cutover(app, client):
    app.config['ADSTERRA_BROWSE_ENABLED'] = True
    for config in ({}, {'ADMIN_SUBDOMAIN_ENABLED': True}):
        app.config.update(config)
        response = client.get('/', base_url=PUBLIC)
        assert SCRIPT not in response.headers['Content-Security-Policy']
        assert b'mauryahub-browse-ads' not in response.data


@pytest.mark.parametrize('path', ['/', '/exam/Quiz%201', '/course/1', '/paper/1'])
def test_browse_shells_embed_one_exact_banner_tag(app, client, path):
    app.config.update(ADSTERRA_BROWSE_ENABLED=True, ADMIN_SUBDOMAIN_ENABLED=True, ADMIN_REDIRECT_ENABLED=True)
    response = client.get(path, base_url=PUBLIC)
    assert response.status_code == 200
    assert response.data.count(b'name="mauryahub-browse-ads" content="active"') == 1
    assert SCRIPT in response.headers['Content-Security-Policy']
    assert f"'sha256-{OPTIONS_HASH}'" in response.headers['Content-Security-Policy']
    assert response.data.count(f'<script src="{SCRIPT}"></script>'.encode()) == 1
    assert b"'format' : 'iframe'" in response.data
    assert b'<iframe' not in response.data
    assert response.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'


def test_other_direct_documents_keep_their_original_ad_policy(app, client):
    app.config.update(ADSTERRA_BROWSE_ENABLED=True, ADMIN_SUBDOMAIN_ENABLED=True, ADMIN_REDIRECT_ENABLED=True)
    for origin, path in [(PUBLIC, '/attempt/1'), (PUBLIC, '/result/1'), (ADMIN, '/admin'), ('https://pyq-test-1.onrender.com', '/')]:
        response = client.get(path, base_url=origin)
        assert SCRIPT not in response.headers['Content-Security-Policy']
        assert b'id="mauryahub-browse-banner"' not in response.data
        assert b'content="active"' not in response.data
