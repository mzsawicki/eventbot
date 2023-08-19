from threading import Thread
from time import sleep
from datetime import datetime

from eventbot.domain import Calendar
from eventbot.infrastructure.persistence import SQLCalendarUnitOfWork


def test_created_calendar_can_be_later_altered(session_factory, fake_clock, fake_sequence_generator, fake_notifier):
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


def test_existence_of_created_calendar_can_be_checked(session_factory, fake_clock,
                                                      fake_sequence_generator, fake_notifier):
    test_guild, test_channel = 'test_guild', 'test_channel'
    calendar = Calendar(test_guild, test_channel)
    with SQLCalendarUnitOfWork(session_factory) as unit_of_work:
        calendar.add_event('Test event, 12 grudnia 2023 o 22', 'Alice#003',
                           fake_clock, fake_sequence_generator, fake_notifier)
        unit_of_work.calendars.add_calendar(calendar)
        unit_of_work.commit()
    with SQLCalendarUnitOfWork(session_factory) as unit_of_work:
        retrieved_calendar_exists = unit_of_work.calendars.does_calendar_exist(test_guild, test_channel)
        assert retrieved_calendar_exists is True


def test_if_calendar_does_not_exist_repository_returns_false(session_factory):
    with SQLCalendarUnitOfWork(session_factory) as unit_of_work:
        calendar_exists = unit_of_work.calendars.does_calendar_exist('test_guild', 'test_channel')
        assert calendar_exists is False


def test_two_parallel_writing_processes_do_not_break_calendar_integrity(session_factory, fake_clock,
                                                                        fake_sequence_generator, fake_notifier):
    test_guild, test_channel = 'test_guild', 'test_channel'
    with SQLCalendarUnitOfWork(session_factory) as unit_of_work:
        unit_of_work.calendars.add_calendar(Calendar(test_guild, test_channel))
        unit_of_work.commit()

    def slow_task(event_prompt: str, user_handle: str) -> None:
        with SQLCalendarUnitOfWork(session_factory) as uow:
            calendar = uow.calendars.get_calendar_by_guild_and_channel(test_guild, test_channel)
            sleep(3)
            calendar.add_event(event_prompt, user_handle,
                               fake_clock, fake_sequence_generator, fake_notifier)
            uow.calendars.add_calendar(calendar)
            uow.commit()

    thread1 = Thread(target=slow_task, args=['Birthday party at 22.02.2024 20:00', 'Sp00k#0022'])
    thread2 = Thread(target=slow_task, args=['Birthday party at 14.01.2024 20:00', 'Sesh#1401'])

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    with SQLCalendarUnitOfWork(session_factory) as unit_of_work:
        calendar = unit_of_work.calendars.get_calendar_by_guild_and_channel(test_guild, test_channel)
        assert calendar._version == 2


def test_repository_returns_incoming_events(session_factory, fake_clock, fake_sequence_generator, fake_notifier):
    fake_clock.set_time(datetime(2022, 1, 1, 12))
    test_guild, test_channel = 'test_guild', 'test_channel'
    with SQLCalendarUnitOfWork(session_factory) as unit_of_work:
        calendar = Calendar(test_guild, test_channel)
        calendar.add_event('Wydarzenie 1 jutro o 10', 'testuser', fake_clock, fake_sequence_generator, fake_notifier)
        calendar.add_event('Wydarzenie 2 jutro o 12', 'testuser', fake_clock, fake_sequence_generator, fake_notifier)
        calendar.add_event('Wydarzenie 3 pojutrze o 12', 'testuser', fake_clock, fake_sequence_generator, fake_notifier)

        unit_of_work.calendars.add_calendar(calendar)
        unit_of_work.commit()

    with SQLCalendarUnitOfWork(session_factory) as unit_of_work:
        events = unit_of_work.calendars.get_incoming_events(test_guild, test_channel)
        assert len(events) == 3
