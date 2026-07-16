from pydantic import BaseModel, Field

from app.privacy.policies import REDACTION_RULES


class ScrubResult(BaseModel):
    text: str
    redaction_count: int = 0
    tags: list[str] = Field(default_factory=list)


def scrub_text(text: str) -> ScrubResult:
    scrubbed = text
    tags: list[str] = []
    redaction_count = 0
    for rule in REDACTION_RULES:
        scrubbed, count = rule.pattern.subn(rule.replacement, scrubbed)
        if count:
            redaction_count += count
            tags.append(rule.tag)
    return ScrubResult(text=scrubbed, redaction_count=redaction_count, tags=tags)
