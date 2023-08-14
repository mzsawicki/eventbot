from datetime import datetime

import pytest

from eventbot.domain import Calendar, CalendarLanguage
from eventbot.infrastructure.persistence import (
    get_database_engine,
    get_session_factory,
    map_tables,
    build_dsn
)

from tests.fakes import FakeClock, FakeNotifier, FakeSequenceGenerator


@pytest.fixture
def fake_clock():
    return FakeClock(datetime(1970, 1, 1))


@pytest.fixture
def fake_notifier():
    return FakeNotifier()


@pytest.fixture
def calendar():
    calendar = Calendar('test_guild', 'test_channel', CalendarLanguage.PL)
    return calendar


@pytest.fixture
def fake_sequence_generator():
    return FakeSequenceGenerator()


@pytest.fixture(scope='session')
def dsn():
    return build_dsn()


@pytest.fixture(scope='session')
def db(dsn):
    yield get_database_engine(dsn)


@pytest.fixture(scope='function')
def session_factory(db):
    map_tables(db)
    yield get_session_factory(db)
