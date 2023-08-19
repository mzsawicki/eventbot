import abc
from datetime import datetime
from typing import List, Generator, Optional


class Notifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify_event_start(self, event_name: str, event_code: str, user_handles: List[str]) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def notify_reminder(self, event_name: str, event_code: str, start_time: datetime, user_handles: List[str]) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def notify_event_created(self, event_name: str, event_code: str, time: datetime, owner: str,
                             reminder_time: Optional[datetime] = None) -> None:
        raise NotImplemented


class Clock(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def now(self) -> datetime:
        raise NotImplemented


class EventSequenceGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self) -> Generator[int, None, None]:
        raise NotImplemented
