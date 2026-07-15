from pydantic import BaseModel, Field

from app.privacy.policies import SENSITIVE_KEYWORDS


class SensitivityResult(BaseModel):
    is_blocked: bool
    tags: list[str] = Field(default_factory=list)


def classify_sensitivity(text: str) -> SensitivityResult:
    lowered = text.lower()
    tags = [
        tag
        for tag, keywords in SENSITIVE_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    ]
    return SensitivityResult(is_blocked=bool(tags), tags=tags)
