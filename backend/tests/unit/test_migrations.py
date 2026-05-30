from backend.services import migrations


def test_run_migrations_skips_when_database_url_missing(monkeypatch):
    monkeypatch.setattr(migrations, "DATABASE_URL", None)
    result = migrations.run_migrations()
    assert result == {"status": "skipped", "reason": "DATABASE_URL not set"}
