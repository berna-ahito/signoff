import json
from unittest.mock import MagicMock, patch

import groq
import pytest
from pydantic import ValidationError

from app.db.models import PurchaseRequest
from app.services.groq_provider import GroqProvider
from app.services.mock_ai_provider import MockAIProvider


def _make_request():
    return PurchaseRequest(
        id=1,
        title="Test Server",
        description="A detailed description of the server hardware needed for our infrastructure",
        category="IT",
        urgency="high",
        quantity=1,
        estimated_cost=8000.0,
        justification="Required for production workload scaling and system reliability",
        status="draft",
        requester_id=1,
        vendor_id=1,
    )


def _valid_groq_payload():
    return {
        "summary": "Purchase of a test server for production.",
        "category": "IT",
        "urgency": "high",
        "risk_level": "medium",
        "missing_info": [],
        "recommended_action": "review",
        "rfq_draft": "Request for Quotation: Test Server, Qty 1, Budget $8000.",
        "confidence": 0.85,
    }


@patch("app.services.groq_provider.groq.Groq")
def test_groq_provider_happy_path(mock_groq_cls):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(_valid_groq_payload())))]
    )

    provider = GroqProvider()
    result = provider.review(_make_request())

    assert result.risk_level == "medium"
    assert result.urgency == "high"
    assert result.confidence == 0.85
    assert result.missing_info == []


@patch("app.services.groq_provider.groq.Groq")
def test_groq_falls_back_on_invalid_json(mock_groq_cls):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="not valid json {{{"))]
    )

    provider = GroqProvider()
    result = provider.review(_make_request())

    mock_result = MockAIProvider().review(_make_request())
    assert result.risk_level == mock_result.risk_level
    assert result.recommended_action == mock_result.recommended_action


@patch("app.services.groq_provider.groq.Groq")
def test_groq_falls_back_on_invalid_literals(mock_groq_cls):
    bad_payload = _valid_groq_payload()
    bad_payload["risk_level"] = "extreme"

    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(bad_payload)))]
    )

    provider = GroqProvider()
    result = provider.review(_make_request())

    assert result.risk_level in ("low", "medium", "high")


@patch("app.services.groq_provider.groq.Groq")
def test_groq_falls_back_on_api_error(mock_groq_cls):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("rate limit exceeded")

    provider = GroqProvider()
    result = provider.review(_make_request())

    assert result.risk_level in ("low", "medium", "high")


