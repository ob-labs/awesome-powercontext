import pytest

from app.services.act_router import ActRouter, UnknownActError


def test_explicit_act_key_wins_over_text():
    assert ActRouter().resolve("Act 6", "我觉得有点冷") == "Act 6"


def test_compatibility_phrase_resolves_vehicle_capability():
    assert ActRouter().resolve(None, "这台车支持小憩模式吗？") == "Act 4"


def test_unknown_phrase_requires_act_key():
    with pytest.raises(UnknownActError):
        ActRouter().resolve(None, "随便聊聊")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("我冬天上车一般 26C，座椅加热 2 档。", "Act 1"),
        ("我夏天上车一般 23C，座椅加热 0 档。", "Act 1"),
        ("有点冷。", "Act 2"),
        ("车里有点热。", "Act 2"),
        ("It feels a bit warm in here.", "Act 2"),
        ("按我上次舒服的设置来。", "Act 3"),
        ("这台车支持小憩模式吗？", "Act 4"),
        ("带我去上周五那家餐厅。", "Act 5"),
        ("确认导航。", "Act 5"),
        ("放点适合孩子睡觉的内容。", "Act 6"),
        ("今晚有什么安排建议？", "Act 7"),
        ("触发雨天通勤或低电量上下文。", "Act 8"),
        ("通过 POST /events/vehicle 触发低电量。", "Act 9"),
        ("跳转到 Day 90。", "Act 10"),
    ],
)
def test_compatibility_phrase_families_cover_all_scripted_acts(text, expected):
    assert ActRouter().resolve(None, text) == expected
