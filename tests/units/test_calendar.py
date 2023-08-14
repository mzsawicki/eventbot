from datetime import datetime, timedelta

import pytest

from eventbot.domain import (
    UserNotPermittedToDeleteEvent,
    EventInThePast,
    UserNotPermittedToSetReminderForEvent,
    EventNotFound,
    ReminderInThePast
)


def test_event_members_are_notified_on_reminder(fake_clock, fake_notifier, calendar, fake_sequence_generator):
    fake_clock.set_time(datetime(2023, 8, 1, 12))

    event_code = calendar.add_event('Wydarzenie testowe, 02.08.2023, 12:30, przypomnienie 10 minut wcześniej',
                                    'Alice#003', fake_clock, fake_sequence_generator, fake_notifier)
    calendar.declare_yes_to_event('Bob#002', event_code)
    calendar.declare_maybe_to_event('Admin#001', event_code)
    calendar.declare_yes_to_event('John#004', event_code)
    calendar.declare_no_to_event('Jane#005', event_code)

    fake_clock.set_time(datetime(2023, 8, 2, 12, 20))
    calendar.send_pending_notifications(fake_clock, fake_notifier)

    assert set(fake_notifier.notified_handles) == {"Alice#003", "Bob#002", "Admin#001", "John#004"}


def test_event_members_are_notified_even_if_reminder_is_late(fake_clock, fake_notifier,
                                                             calendar, fake_sequence_generator):
    fake_clock.set_time(datetime(2023, 9, 13))

    event_code = calendar.add_event('Test, 30 września 2023 o 18. Przypomnienie 30 minut wcześniej',
                                    'John#004', fake_clock, fake_sequence_generator, fake_notifier)
    calendar.declare_yes_to_event('Alice#003', event_code)

    fake_clock.set_time(datetime(2023, 9, 30, 17, 55))
    calendar.send_pending_notifications(fake_clock, fake_notifier)

    assert set(fake_notifier.notified_handles) == {'John#004', 'Alice#003'}


def test_user_cannot_delete_event_of_another_user(fake_clock, calendar, fake_sequence_generator, fake_notifier):
    fake_clock.set_time(datetime(2023, 1, 1, 19))
    event_code = calendar.add_event('Test, 3 stycznia 2023 o 17.00', 'Alice#003',
                                    fake_clock, fake_sequence_generator, fake_notifier)
    with pytest.raises(UserNotPermittedToDeleteEvent):
        calendar.delete_event('John#004', event_code)


def test_users_cannot_add_events_in_the_past(fake_clock, calendar, fake_sequence_generator, fake_notifier):
    fake_clock.set_time(datetime(2023, 4, 4, 14, 15))
    with pytest.raises(EventInThePast):
        calendar.add_event('Test event, 3.04.2023 o 12', 'Admin#001',
                           fake_clock, fake_sequence_generator, fake_notifier)


def test_user_cannot_set_reminder_for_event_of_another_user(fake_clock, calendar,
                                                            fake_sequence_generator, fake_notifier):
    fake_clock.set_time(datetime(2023, 2, 1, 21, 37))
    event_code = calendar.add_event('Test event, 2 lutego 2023 21:37', 'Alice#003',
                                    fake_clock, fake_sequence_generator, fake_notifier)
    with pytest.raises(UserNotPermittedToSetReminderForEvent):
        calendar.set_reminder_for_event('Admin#001', event_code, timedelta(hours=1))


def test_user_can_set_reminder_for_own_event_after_creation(fake_clock, calendar,
                                                            fake_notifier, fake_sequence_generator):
    fake_clock.set_time(datetime(2023, 11, 30, 11))
    event_code = calendar.add_event('Test event pierwszego grudnia o 12', 'Jane#005',
                                    fake_clock, fake_sequence_generator, fake_notifier)
    calendar.declare_yes_to_event('John#004', event_code)
    fake_clock.progress(timedelta(hours=13))
    calendar.set_reminder_for_event('Jane#005', event_code, timedelta(hours=1))
    fake_clock.progress(timedelta(hours=11))
    calendar.send_pending_notifications(fake_clock, fake_notifier)
    assert set(fake_notifier.notified_handles) == {'John#004', 'Jane#005'}


def test_user_can_re_set_reminder_time(fake_clock, calendar, fake_notifier, fake_sequence_generator):
    fake_clock.set_time(datetime(2023, 6, 6, 12, 34, 52))
    event_code = calendar.add_event('Test event 7.6.2023 o 12, przypomnienie 2 godziny wcześniej', 'Alice#003',
                                    fake_clock, fake_sequence_generator, fake_notifier)
    calendar.declare_yes_to_event('Bob#002', event_code)
    calendar.set_reminder_for_event('Alice#003', event_code, timedelta(hours=3))
    fake_clock.set_time(datetime(2023, 6, 7, 9))
    calendar.send_pending_notifications(fake_clock, fake_notifier)
    assert set(fake_notifier.notified_handles) == {'Alice#003', 'Bob#002'}


def test_users_are_not_reminded_too_early_when_reminder_is_re_set(fake_clock, calendar, fake_notifier,
                                                                  fake_sequence_generator):
    fake_clock.set_time(datetime(2023, 12, 23, 13, 1, 22))
    event_code = calendar.add_event('Test event, 24 grudnia 2023 o 12, przypomnienie 3 godziny wcześniej', 'Alice#003',
                                    fake_clock, fake_sequence_generator, fake_notifier)
    fake_notifier.clear()
    calendar.declare_yes_to_event('Bob#002', event_code)
    fake_clock.progress(timedelta(hours=3))
    calendar.set_reminder_for_event('Alice#003', event_code, timedelta(hours=1))
    fake_clock.set_time(datetime(2023, 12, 24, 10, 30))
    calendar.send_pending_notifications(fake_clock, fake_notifier)
    assert set(fake_notifier.notified_handles) == set()


def test_cannot_set_reminder_for_non_existent_event(fake_clock, calendar, fake_notifier):
    fake_clock.set_time(datetime(2023, 5, 3, 15, 32, 10))
    with pytest.raises(EventNotFound):
        calendar.set_reminder_for_event('Admin#001', 'tes-1', timedelta(hours=1))


def test_cannot_set_reminder_in_the_past(fake_clock, calendar, fake_sequence_generator, fake_notifier):
    fake_clock.set_time(datetime(2023, 6, 6, 12, 34, 52))
    with pytest.raises(ReminderInThePast):
        calendar.add_event('Testowe, 7/06/2023, 12.00, przypomnij 3 dni wcześniej', 'Alice#003',
                           fake_clock, fake_sequence_generator, fake_notifier)


def test_users_are_reminded_only_once(fake_clock, fake_notifier, calendar, fake_sequence_generator):
    fake_clock.set_time(datetime(2023, 10, 11, 13, 44, 23))
    calendar.add_event('Wydarzenie 18.10.2023 o ósmej wieczorem. Przypomnienie godzinę wcześniej', 'Alice#003',
                       fake_clock, fake_sequence_generator, fake_notifier)
    fake_clock.set_time(datetime(2023, 10, 18, 19, 1))
    calendar.send_pending_notifications(fake_clock, fake_notifier)
    notified_handles_1 = fake_notifier.notified_handles
    fake_notifier.clear()
    fake_clock.progress(timedelta(minutes=1))
    calendar.send_pending_notifications(fake_clock, fake_notifier)
    notified_handles_2 = fake_notifier.notified_handles
    assert notified_handles_1 == ['Alice#003'] and notified_handles_2 == []


def test_users_are_notified_on_event_start_only_once(fake_clock, fake_notifier, calendar, fake_sequence_generator):
    fake_clock.set_time(datetime(2023, 10, 11, 13, 44, 23))
    calendar.add_event('Test event, 18 października 2023, o dwudziestej', 'Alice#003',
                       fake_clock, fake_sequence_generator, fake_notifier)
    fake_clock.set_time(datetime(2023, 10, 18, 20))
    calendar.send_pending_notifications(fake_clock, fake_notifier)
    notified_handles_1 = fake_notifier.notified_handles
    fake_notifier.clear()
    fake_clock.progress(timedelta(minutes=1))
    calendar.send_pending_notifications(fake_clock, fake_notifier)
    notified_handles_2 = fake_notifier.notified_handles
    assert notified_handles_1 == ['Alice#003'] and notified_handles_2 == []


def test_the_owner_is_notified_at_event_creation(fake_clock, fake_notifier, calendar, fake_sequence_generator):
    fake_clock.set_time(datetime(2025, 3, 23, 11, 44, 16))
    calendar.add_event('Test event 24.03.2025, o 12', 'Alice#003', fake_clock,
                       fake_sequence_generator, fake_notifier)
    notified_handles = fake_notifier.notified_handles
    assert notified_handles == ['Alice#003', ]
