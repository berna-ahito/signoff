import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def notify_slack(event: str, request_id: int, title: str, detail: str) -> None:
    if not settings.slack_webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set, skipping notification")
        return
    text = f"[ProcureFlow] *{event}* | Request #{request_id}: {title} | {detail}"
    try:
        httpx.post(settings.slack_webhook_url, json={"text": text}, timeout=5)
    except Exception as exc:
        logger.warning("Slack notification failed: %s", exc)
