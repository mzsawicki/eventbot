from datetime import datetime

from eventbot.domain import Calendar
from eventbot.infrastructure.persistence import SQLCalendarUnitOfWork


def test_created_calendar_can_be_later_retrieved(session_factory, fake_clock, fake_sequence_generator, fake_notifier):
    test_guild, test_channel = 'test_guild', 'test_channel'
    calendar = Calendar(test_guild, test_channel)
    with SQLCalendarUnitOfWork(session_factory) as unit_of_work:
        event_code = calendar.add_event('Test event, 12 grudnia 2023 o 22', 'Alice#003',
                                        fake_clock, fake_sequence_generator, fake_notifier)
        unit_of_work.calendars.add_calendar(calendar)
        unit_of_work.commit()
    with SQLCalendarUnitOfWork(session_factory) as unit_of_work:
        retrieved_calendar = unit_of_work.calendars.get_calendar_by_guild_and_channel(test_guild, test_channel)
        retrieved_calendar.delete_event('Alice#003', event_code)
        unit_of_work.commit()
