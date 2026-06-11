import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, *, to: str, subject: str, body: str) -> None: ...


class MockNotificationProvider(NotificationProvider):
    def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info("[MockNotification] to=%s subject=%s", to, subject)


class ResendProvider(NotificationProvider):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def send(self, *, to: str, subject: str, body: str) -> None:
        import httpx
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"from": "noreply@procureflow.ai", "to": to, "subject": subject, "html": body},
            timeout=10,
        )
        resp.raise_for_status()


def get_notification_provider() -> NotificationProvider:
    from app.core.config import settings
    if settings.resend_api_key:
        return ResendProvider(settings.resend_api_key)
    return MockNotificationProvider()


def notify_request_submitted(request_title: str, approver_emails: list[str]) -> None:
    provider = get_notification_provider()
    for email in approver_emails:
        provider.send(
            to=email,
            subject=f"New procurement request: {request_title}",
            body=f"<p>A new procurement request <b>{request_title}</b> has been submitted for your review.</p>",
        )


def notify_decision_made(request_title: str, decision: str, requester_email: str) -> None:
    provider = get_notification_provider()
    provider.send(
        to=requester_email,
        subject=f"Decision on your request: {request_title}",
        body=f"<p>Your request <b>{request_title}</b> has been <b>{decision}</b>.</p>",
    )
