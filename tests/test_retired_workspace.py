def test_retired_workspace_has_no_registered_routes(app):
    assert not any('/oppe' in rule.rule for rule in app.url_map.iter_rules())
