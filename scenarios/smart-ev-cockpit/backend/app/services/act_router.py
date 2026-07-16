import re
from typing import cast

from app.domain.scenario_models import ActKey

_ACT_KEYS = frozenset(
    {
        "Act 1",
        "Act 2",
        "Act 3",
        "Act 4",
        "Act 5",
        "Act 6",
        "Act 7",
        "Act 8",
        "Act 9",
        "Act 10",
        "Chat",
    }
)

_SCRIPTED_PHRASE_FAMILIES: tuple[tuple[ActKey, tuple[str, ...]], ...] = (
    (
        "Act 1",
        (
            "冬天上车一般 26c",
            "冬天上车一般26c",
            "夏天上车一般 23c",
            "夏天上车一般23c",
            "usually set 26c and seat heat level 2 in winter",
            "usually set 23c and seat heat level 0 in summer",
        ),
    ),
    (
        "Act 2",
        (
            "有点冷",
            "有点凉",
            "有点热",
            "i feel cold",
            "i feel warm",
            "a bit hot",
            "a bit warm",
            "a little cool",
        ),
    ),
    (
        "Act 3",
        ("按我上次舒服的设置来", "use my previous comfort setup"),
    ),
    (
        "Act 4",
        ("支持小憩模式吗", "does this vehicle support rest mode"),
    ),
    (
        "Act 5",
        (
            "带我去上周五那家餐厅",
            "确认导航",
            "开始导航",
            "确认路线",
            "take me to the restaurant from last friday",
            "confirm navigation",
            "start navigation",
            "confirm route",
        ),
    ),
    (
        "Act 6",
        ("放点适合孩子睡觉的内容", "play something for the child to sleep"),
    ),
    ("Act 7", ("今晚有什么安排建议", "any plan for tonight")),
    ("Act 8", ("雨天通勤", "rainy commute", "驾驶模式建议", "driving mode suggestion")),
    (
        "Act 9",
        (
            "post /events/vehicle",
            "主动关怀",
            "proactive care",
        ),
    ),
    ("Act 10", ("day 90", "第90天", "生命周期与隐私", "lifecycle and privacy")),
)


class UnknownActError(ValueError):
    pass


class ActRouter:
    def resolve(self, act_key: ActKey | None, text: str) -> ActKey:
        if act_key is not None:
            if act_key not in _ACT_KEYS:
                raise UnknownActError(f"Unknown act key: {act_key}")
            return cast(ActKey, act_key)

        normalized = _normalize(text)
        for candidate, phrases in _SCRIPTED_PHRASE_FAMILIES:
            if any(phrase in normalized for phrase in phrases):
                return candidate
        raise UnknownActError("An explicit act_key is required for unknown text")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()
