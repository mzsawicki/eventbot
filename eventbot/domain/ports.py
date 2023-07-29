import abc
from datetime import datetime
from typing import Generator, List


class EventSequenceGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self) -> Generator[int, None, None]:
        raise NotImplemented


class Clock(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def now(self) -> datetime:
        raise NotImplemented


class EventReminderNotifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify(self, event_name: str, event_time: datetime, user_handles: List[str]) -> None:
        raise NotImplemented
