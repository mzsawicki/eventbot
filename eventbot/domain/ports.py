import abc
from datetime import datetime
from typing import List, Generator


class Notifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify(self, message: str, user_handles: List[str]) -> None:
        raise NotImplemented


class Clock(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def now(self) -> datetime:
        raise NotImplemented


class EventSequenceGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self) -> Generator[int, None, None]:
        raise NotImplemented
