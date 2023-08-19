from typing import Generator

from eventbot.domain import EventSequenceGenerator
from eventbot.infrastructure.persistence.tables import EVENT_SEQUENCE_NAME

from sqlalchemy import Sequence
from sqlalchemy.orm import Session


class SQLEventSequenceGenerator(EventSequenceGenerator):
    def __init__(self, session: Session):
        self._session = session

    def __call__(self) -> Generator[int, None, None]:
        sequence = Sequence(EVENT_SEQUENCE_NAME)
        next_value = self._session.execute(sequence)
        yield next_value
