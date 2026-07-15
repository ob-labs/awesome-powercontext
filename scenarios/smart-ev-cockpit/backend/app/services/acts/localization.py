import re
from typing import Literal

from app.services.acts.base import ActContext

Locale = Literal["en", "zh"]

_HAN_RE = re.compile(r"[\u4e00-\u9fff]")


def locale_for_text(text: str) -> Locale:
    return "zh" if _HAN_RE.search(text) else "en"


def locale_for_context(context: ActContext) -> Locale:
    return locale_for_text(context.request.text)


def localized(locale: Locale, *, en: str, zh: str) -> str:
    return zh if locale == "zh" else en
