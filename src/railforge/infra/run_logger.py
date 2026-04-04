from railforge.artifacts.store import ArtifactStore


class RunLogger:
    def __init__(self, store: ArtifactStore) -> None:
        self.store = store

    def append(self, message: str) -> None:
        self.store.record_progress(message)

