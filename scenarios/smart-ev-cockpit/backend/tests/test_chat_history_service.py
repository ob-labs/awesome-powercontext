from app.services.chat_history_service import ChatHistoryService


def test_chat_history_persists_messages_by_actor(tmp_path):
    service = ChatHistoryService(tmp_path / "chat.sqlite3")

    driver_user = service.append_message(
        session_id="demo_session_001",
        actor_id="driver_primary",
        seat_position="front_left",
        role="user",
        text="I feel cold.",
        trace_id="trace_driver",
        created_at="2026-07-09T10:00:00Z",
    )
    service.append_message(
        session_id="demo_session_001",
        actor_id="passenger_front",
        seat_position="front_right",
        role="user",
        text="Play something quiet.",
        trace_id="trace_passenger",
        created_at="2026-07-09T10:00:01Z",
    )
    driver_assistant = service.append_message(
        session_id="demo_session_001",
        actor_id="driver_primary",
        seat_position="front_left",
        role="assistant",
        text="Raising the driver zone temperature.",
        trace_id="trace_driver",
        created_at="2026-07-09T10:00:02Z",
    )

    driver_messages = service.list_messages(
        session_id="demo_session_001",
        actor_id="driver_primary",
    )

    assert [message.id for message in driver_messages] == [
        driver_user.id,
        driver_assistant.id,
    ]
    assert [message.role for message in driver_messages] == ["user", "assistant"]
    assert [message.text for message in driver_messages] == [
        "I feel cold.",
        "Raising the driver zone temperature.",
    ]
    assert all(message.actor_id == "driver_primary" for message in driver_messages)


def test_chat_history_limits_latest_messages_in_chronological_order(tmp_path):
    service = ChatHistoryService(tmp_path / "chat.sqlite3")

    for index in range(4):
        service.append_message(
            session_id="demo_session_001",
            actor_id="child_rear_left",
            seat_position="rear_left",
            role="user",
            text=f"message {index}",
            trace_id=f"trace_{index}",
            created_at=f"2026-07-09T10:00:0{index}Z",
        )

    messages = service.list_messages(
        session_id="demo_session_001",
        actor_id="child_rear_left",
        limit=2,
    )

    assert [message.text for message in messages] == ["message 2", "message 3"]
