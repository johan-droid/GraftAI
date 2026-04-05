from backend.api.main import app


def test_critical_routes_are_registered():
    routes = {route.path for route in app.routes}

    assert "/api/v1/analytics/realtime" in routes
    assert "/api/v1/auth/integrations/status" in routes
    assert "/api/v1/calendar/sync" in routes
    assert "/api/v1/notifications/test" in routes