from datetime import datetime, timedelta
from typing import Generator, List, Optional

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
        self._current_value += 1
        yield self._current_value


class FakeNotifier(Notifier):
    def __init__(self):
        self._notified_handles: List[str] = []

    def notify_event_start(self, event_name: str, event_code: str, user_handles: List[str]) -> None:
        self._notified_handles = user_handles

    def notify_reminder(self, event_name: str, event_code: str, start_time: datetime,
                        user_handles: List[str]) -> None:
        self._notified_handles = user_handles

    def notify_event_created(self, event_name: str, event_code: str, time: datetime, owner: str,
                             reminder_time: Optional[datetime] = None) -> None:
        self._notified_handles = [owner, ]

    def clear(self) -> None:
        self._notified_handles = []

    @property
    def notified_handles(self) -> List[str]:
        return self._notified_handles
