import abc

from eventbot.application.repositories import CalendarRepository


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

    @abc.abstractmethod
    def commit(self) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def rollback(self) -> None:
        raise NotImplemented
