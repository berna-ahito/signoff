from app.db.models import PurchaseRequest
from app.schemas.ai_review import AIReviewResult
from app.services.mock_ai_provider import MockAIProvider

_provider = MockAIProvider()


def generate_ai_review(request: PurchaseRequest) -> AIReviewResult:
    return _provider.review(request)
