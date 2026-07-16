from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.privacy.classifiers import classify_sensitivity
from app.privacy.projection import project_memory_for_frontend
from app.privacy.scrubber import scrub_text


def test_scrub_text_masks_address_phone_and_vehicle_identifier():
    result = scrub_text("Call 13812345678 and drive to 123 Lake Rd with plate ABC1234.")

    assert "13812345678" not in result.text
    assert "123 Lake Rd" not in result.text
    assert "ABC1234" not in result.text
    assert result.redaction_count == 3
    assert set(result.tags) == {"phone", "exact_address", "vehicle_identifier"}


def test_scrub_text_masks_chinese_address_identity_card_and_vehicle_plate():
    result = scrub_text(
        "地址是上海市浦东新区世纪大道100号，身份证31010119900101123X，车牌沪A12345。"
    )

    assert "上海市浦东新区世纪大道100号" not in result.text
    assert "31010119900101123X" not in result.text
    assert "沪A12345" not in result.text
    assert result.redaction_count == 3
    assert set(result.tags) == {"exact_address", "identity_card", "vehicle_plate"}


def test_scrub_text_leaves_common_chinese_values_unchanged():
    text = "上海今天气温22度，日期是2026-07-10，车型是蔚来ET5 Touring。"

    result = scrub_text(text)

    assert result.text == text
    assert result.redaction_count == 0
    assert result.tags == []


def test_scrub_text_leaves_invalid_identity_like_business_numbers_unchanged():
    text = (
        "业务编号990000202613401234，"
        "非法日期证件号31010120230229123X，"
        "非法末位证件号31010119900101123A，"
        "字母数字包围A31010119900101123XZ。"
    )

    result = scrub_text(text)

    assert result.text == text
    assert result.redaction_count == 0
    assert result.tags == []


def test_classifier_blocks_sensitive_domains():
    result = classify_sensitivity("My medical bill and bank password are in the glovebox.")

    assert result.is_blocked is True
    assert set(result.tags) == {"health", "finance", "credential"}


def test_projection_hides_masked_memory_content():
    memory = MemoryRecord(
        memory_id="mem_001",
        content="passenger_front has an anniversary with driver_primary on 10-03.",
        metadata=MemoryMetadata(
            actor_id="passenger_front",
            memory_kind="relationship_event",
            memory_dimension=["episodic"],
            visibility="masked",
            privacy_level="masked",
            source_event_ids=["rel_0001"],
            created_at="2026-01-01T00:00:00Z",
            is_sensitive=True,
        ),
    )

    projection = project_memory_for_frontend(memory)

    assert projection["memory_id"] == "mem_001"
    assert projection["content"] == "Masked relationship_event memory"
    assert projection["hidden_fields"] == ["sensitive_content"]
