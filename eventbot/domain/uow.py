import abc

from eventbot.domain.repositories import CalendarRepository
from eventbot.domain.ports import EventSequenceGenerator


class CalendarUnitOfWork(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __enter__(self) -> 'CalendarUnitOfWork':
        raise NotImplemented

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        raise NotImplemented

    @property
    @abc.abstractmethod
    def calendars(self) -> CalendarRepository:
        raise NotImplemented

    @property
    @abc.abstractmethod
    def event_sequence_generator(self) -> EventSequenceGenerator:
        raise NotImplemented

    @abc.abstractmethod
    def commit(self) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def rollback(self) -> None:
        raise NotImplemented
