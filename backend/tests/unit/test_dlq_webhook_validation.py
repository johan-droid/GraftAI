from backend.services.dlq_handlers import _validate_webhook_url, _validate_teams_webhook_url

def test_validate_webhook_url():
    assert _validate_webhook_url("https://example.com") == True
    assert _validate_webhook_url("http://example.com", allow_localhost=False) == False
    assert _validate_webhook_url("http://localhost:8000", allow_localhost=True) == True
    assert _validate_webhook_url("http://169.254.169.254") == False

def test_validate_teams_webhook_url():
    assert _validate_teams_webhook_url("https://outlook.office.com/webhook/123") == True
    assert _validate_teams_webhook_url("https://malicious-office.com") == False
    assert _validate_teams_webhook_url("https://malicious-microsoft.com") == False
