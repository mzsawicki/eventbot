from datetime import datetime, timedelta
from typing import Generator, List

from eventbot.domain import Clock, EventSequenceGenerator, Notifier


class FakeClock(Clock):
    def __init__(self, custom_time: datetime):
        self._now: datetime = custom_time

    def now(self) -> datetime:
        return self._now

    def set_time(self, time: datetime) -> None:
        self._now = time

    def progress(self, delta: timedelta) -> None:
        self._now += delta


class FakeSequenceGenerator(EventSequenceGenerator):
    def __init__(self):
        self._current_value: int = 0

    def __call__(self) -> Generator[int, None, None]:
        yield self._current_value
        self._current_value += 1


class FakeNotifier(Notifier):
    def __init__(self):
        self._notified_handles: List[str] = []

    def notify(self, message: str, user_handles: List[str]) -> None:
        self._notified_handles = user_handles

    @property
    def notified_handles(self) -> List[str]:
        return self._notified_handles
