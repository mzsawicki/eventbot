from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

from eventbot.domain import CalendarUnitOfWork
from eventbot.infrastructure.persistence.repositories import SQLCalendarRepository
from eventbot.infrastructure.persistence.sequence_generator import SQLEventSequenceGenerator


class SQLCalendarUnitOfWork(CalendarUnitOfWork):
    def __init__(self, session_factory: sessionmaker):
        self._session_factory: sessionmaker = session_factory
        self._session: Optional[Session] = None
        self._calendars: Optional[SQLCalendarRepository] = None
        self._event_sequence_generator: Optional[SQLEventSequenceGenerator] = None

    @property
    def calendars(self) -> SQLCalendarRepository:
        if self._calendars is not None:
            return self._calendars
        raise Exception('Attempt to use repository outside database session')

    @property
    def event_sequence_generator(self) -> SQLEventSequenceGenerator:
        if self._event_sequence_generator is not None:
            return self._event_sequence_generator
        raise Exception('Attempt to use sequence generator outside database session')

    def __enter__(self) -> 'CalendarUnitOfWork':
        self._session = self._session_factory()
        self._calendars = SQLCalendarRepository(self._session)
        self._event_sequence_generator = SQLEventSequenceGenerator(self._session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
