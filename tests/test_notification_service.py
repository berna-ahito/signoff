from app.services.notification_service import (
    MockNotificationProvider,
    notify_decision_made,
    notify_request_submitted,
)


def test_request_submitted_calls_provider(monkeypatch):
    calls = []

    class SpyProvider(MockNotificationProvider):
        def send(self, *, to, subject, body):
            calls.append({"to": to, "subject": subject})

    monkeypatch.setattr(
        "app.services.notification_service.get_notification_provider", lambda: SpyProvider()
    )
    notify_request_submitted("New Laptop", ["manager@test.com"])
    assert len(calls) == 1
    assert calls[0]["to"] == "manager@test.com"
    assert "New Laptop" in calls[0]["subject"]


def test_decision_made_calls_provider(monkeypatch):
    calls = []

    class SpyProvider(MockNotificationProvider):
        def send(self, *, to, subject, body):
            calls.append({"to": to, "subject": subject})

    monkeypatch.setattr(
        "app.services.notification_service.get_notification_provider", lambda: SpyProvider()
    )
    notify_decision_made("New Laptop", "approved", "alice@test.com")
    assert len(calls) == 1
    assert calls[0]["to"] == "alice@test.com"
    assert "New Laptop" in calls[0]["subject"]


def test_request_submitted_multiple_approvers(monkeypatch):
    calls = []

    class SpyProvider(MockNotificationProvider):
        def send(self, *, to, subject, body):
            calls.append({"to": to})

    monkeypatch.setattr(
        "app.services.notification_service.get_notification_provider", lambda: SpyProvider()
    )
    notify_request_submitted("Office Chairs", ["mgr1@test.com", "mgr2@test.com"])
    assert len(calls) == 2
    assert {c["to"] for c in calls} == {"mgr1@test.com", "mgr2@test.com"}


def test_request_submitted_no_approvers(monkeypatch):
    calls = []

    class SpyProvider(MockNotificationProvider):
        def send(self, *, to, subject, body):
            calls.append({"to": to})

    monkeypatch.setattr(
        "app.services.notification_service.get_notification_provider", lambda: SpyProvider()
    )
    notify_request_submitted("Empty List", [])
    assert len(calls) == 0


def test_mock_provider_logs_without_error():
    provider = MockNotificationProvider()
    # Should not raise
    provider.send(to="x@test.com", subject="Test", body="<p>Hello</p>")


def test_get_notification_provider_returns_mock_when_no_key(monkeypatch):
    from app.services.notification_service import (
        MockNotificationProvider,
        get_notification_provider,
    )

    monkeypatch.setattr("app.core.config.settings.resend_api_key", "")
    provider = get_notification_provider()
    assert isinstance(provider, MockNotificationProvider)


def test_get_notification_provider_returns_resend_when_key_set(monkeypatch):
    from app.services.notification_service import ResendProvider, get_notification_provider

    monkeypatch.setattr("app.core.config.settings.resend_api_key", "re_test_key")
    provider = get_notification_provider()
    assert isinstance(provider, ResendProvider)
