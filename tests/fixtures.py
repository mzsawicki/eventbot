from datetime import datetime

import pytest

from tests.fakes import FakeClock, FakeEventReminderNotifier, FakeSequenceGenerator
from eventbot.domain import Calendar, EventCodeProvider


@pytest.fixture
def clock():
    return FakeClock(datetime(1970, 1, 1))


@pytest.fixture
def notifier():
    return FakeEventReminderNotifier()


@pytest.fixture
def calendar(clock, notifier):
    calendar = Calendar('test_channel', clock, notifier, EventCodeProvider(FakeSequenceGenerator()))
    calendar.add_user('Admin#001', is_admin=True)
    calendar.add_user('Bob#002', event_creation_enabled=False)
    calendar.add_user('Alice#003')
    calendar.add_user('John#004')
    calendar.add_user('Jane#005')
    return calendar
