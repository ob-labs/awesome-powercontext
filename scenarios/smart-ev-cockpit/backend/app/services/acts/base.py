from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.scenario_models import ActRequest, ActResult

SAFE_REGION_LABELS = {
    "浦东新区": "浦东新区",
    "虹桥商务区": "虹桥商务区",
    "浦东滨江": "浦东滨江",
    "张江科学城": "张江科学城",
    "城西片区": "虹桥商务区",
    "滨河片区": "浦东滨江",
    "北部科技园": "张江科学城",
    "pudong new area": "Pudong New Area",
    "hongqiao business district": "Hongqiao Business District",
    "pudong riverside": "Pudong Riverside",
    "zhangjiang science city": "Zhangjiang Science City",
    "river district": "River District",
    "west city": "West City",
    "west city area": "Hongqiao Business District",
    "north tech park": "Zhangjiang Science City",
}


@dataclass(frozen=True)
class ActContext:
    request: ActRequest
    container: Any


class ActHandler(Protocol):
    def handle(self, context: ActContext) -> ActResult: ...


def safe_region_label(value: str | None) -> str | None:
    normalized = " ".join((value or "").casefold().split())
    return SAFE_REGION_LABELS.get(normalized)


def safe_region_label_from_text(value: str | None) -> str | None:
    normalized = " ".join((value or "").casefold().split())
    return next(
        (
            label
            for region, label in SAFE_REGION_LABELS.items()
            if region.casefold() in normalized
        ),
        None,
    )
