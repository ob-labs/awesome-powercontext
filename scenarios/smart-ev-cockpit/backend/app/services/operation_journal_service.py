class OperationJournalService:
    def __init__(self):
        self._operations: list[dict] = []

    def append(self, operation: dict) -> None:
        self._operations.append(operation)

    def recent(self, limit: int = 20) -> list[dict]:
        return self._operations[-limit:]
