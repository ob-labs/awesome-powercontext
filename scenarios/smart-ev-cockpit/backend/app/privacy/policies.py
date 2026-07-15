import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RedactionRule:
    tag: str
    pattern: re.Pattern[str]
    replacement: str


REDACTION_RULES = [
    RedactionRule("phone", re.compile(r"\b1[3-9]\d{9}\b"), "[REDACTED_PHONE]"),
    RedactionRule(
        "exact_address",
        re.compile(r"\b\d{1,5}\s+[A-Z][A-Za-z]+\s+(Rd|Road|St|Street|Ave|Avenue)\b"),
        "[REDACTED_ADDRESS]",
    ),
    RedactionRule(
        "exact_address",
        re.compile(
            r"(?:(?:北京|上海|天津|重庆)市|"
            r"(?:[\u4e00-\u9fff]{2,6}省)?[\u4e00-\u9fff]{2,6}市)"
            r"[\u4e00-\u9fff]{2,8}(?:区|县)"
            r"[\u4e00-\u9fff]{2,12}(?:路|街|道|巷)\d{1,6}号"
        ),
        "[REDACTED_ADDRESS]",
    ),
    RedactionRule(
        "identity_card",
        re.compile(
            r"(?<![A-Za-z0-9])"
            r"(?:11|12|13|14|15|21|22|23|31|32|33|34|35|36|37|"
            r"41|42|43|44|45|46|50|51|52|53|54|61|62|63|64|65|71|81|82)"
            r"\d{4}"
            r"(?:"
            r"(?:18|19|20)\d{2}"
            r"(?:"
            r"(?:0[13578]|1[02])(?:0[1-9]|[12]\d|3[01])|"
            r"(?:0[469]|11)(?:0[1-9]|[12]\d|30)|"
            r"02(?:0[1-9]|1\d|2[0-8])"
            r")|"
            r"(?:18(?:0[48]|[2468][048]|[13579][26])|"
            r"19(?:0[48]|[2468][048]|[13579][26])|"
            r"20(?:0[48]|[2468][048]|[13579][26])|2000)0229"
            r")"
            r"\d{3}[\dXx]"
            r"(?![A-Za-z0-9])"
        ),
        "[REDACTED_IDENTITY_CARD]",
    ),
    RedactionRule(
        "vehicle_plate",
        re.compile(
            r"(?<![A-Z0-9])"
            r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]"
            r"[A-HJ-NP-Z][A-HJ-NP-Z0-9]{5}(?![A-Z0-9])"
        ),
        "[REDACTED_VEHICLE_PLATE]",
    ),
    RedactionRule("vehicle_identifier", re.compile(r"\b[A-Z]{3}\d{4}\b"), "[REDACTED_VEHICLE_ID]"),
]

SENSITIVE_KEYWORDS = {
    "health": ["medical", "diagnosis", "prescription"],
    "finance": ["bank", "bill", "payment card"],
    "legal": ["lawsuit", "court order"],
    "credential": ["password", "token", "secret key"],
}
