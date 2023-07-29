from datetime import datetime, timedelta

import pytest

from eventbot.domain import (
    UserForbiddenFromCreatingEvents,
    UserNotPermittedToDeleteEvent,
    EventInThePast,
    UserNotFound,
    UserNotPermittedToSetReminderForEvent,
    EventNotFound
)


def test_event_members_are_notified_on_reminder(clock, notifier, calendar):
    clock.set_time(datetime(2023, 8, 1, 12))

    event = calendar.add_event('Test event', datetime(2023, 8, 2, 12, 30), 'Alice#003', timedelta(minutes=10))
    calendar.declare_joining_event('Bob#002', event.code)
    calendar.declare_uncertain_for_event('Admin#001', event.code)
    calendar.declare_joining_event('John#004', event.code)
    calendar.declare_declined_event('Jane#005', event.code)

    clock.set_time(datetime(2023, 8, 2, 12, 20))
    calendar.notify_for_pending_reminders()

    assert set(notifier.notified_handles) == {"Alice#003", "Bob#002", "Admin#001", "John#004"}


def test_event_members_are_notified_even_if_reminder_is_late(clock, notifier, calendar):
    clock.set_time(datetime(2023, 9, 13))

    event = calendar.add_event('Test event', datetime(2023, 9, 30, 18), 'John#004', timedelta(minutes=30))
    calendar.declare_joining_event('Alice#003', event.code)

    clock.set_time(datetime(2023, 9, 30, 17, 55))
    calendar.notify_for_pending_reminders()

    assert set(notifier.notified_handles) == {'John#004', 'Alice#003'}


def test_user_cannot_delete_event_of_another_user(clock, calendar):
    clock.set_time(datetime(2023, 1, 1, 19))
    event = calendar.add_event('Test event', datetime(2023, 1, 3, 17), 'Alice#003')
    with pytest.raises(UserNotPermittedToDeleteEvent):
        calendar.delete_event('John#004', event.code)


def test_admin_can_delete_event_of_another_user(clock, calendar):
    clock.set_time(datetime(2023, 1, 1, 19))
    event = calendar.add_event('Test event', datetime(2023, 1, 3, 17), 'Alice#003')
    calendar.delete_event('Admin#001', event.code)


def test_user_forbidden_from_creating_events_cannot_create_them(clock, calendar):
    clock.set_time(datetime(2023, 8, 1, 12))
    with pytest.raises(UserForbiddenFromCreatingEvents):
        calendar.add_event('Test event', datetime(2023, 8, 8, 20), 'Bob#002')


def test_users_cannot_add_events_in_the_past(clock, calendar):
    clock.set_time(datetime(2023, 4, 4, 14, 15))
    with pytest.raises(EventInThePast):
        calendar.add_event('Test event', datetime(2023, 4, 3, 12), 'Admin#001')


def test_event_creation_fails_if_user_handle_unknown(clock, calendar):
    clock.set_time(datetime(2024, 3, 23, 11, 32, 22))
    with pytest.raises(UserNotFound):
        calendar.add_event('Test event', datetime(2024, 4, 11, 12), 'Notfound#000')


def test_user_cannot_set_reminder_for_event_of_another_user(clock, calendar):
    clock.set_time(datetime(2023, 2, 1, 21, 37))
    event = calendar.add_event('Test event', datetime(2023, 2, 2, 20), 'Alice#003')
    with pytest.raises(UserNotPermittedToSetReminderForEvent):
        calendar.set_event_reminder('Admin#001', event.code, timedelta(hours=1))


def test_user_can_set_reminder_for_own_event_after_creation(clock, calendar, notifier):
    clock.set_time(datetime(2023, 11, 30, 11))
    event = calendar.add_event('Test event', datetime(2023, 12, 1, 12), 'Jane#005')
    calendar.declare_joining_event('John#004', event.code)
    clock.progress(timedelta(hours=13))
    calendar.set_event_reminder('Jane#005', event.code, timedelta(hours=1))
    clock.progress(timedelta(hours=11))
    calendar.notify_for_pending_reminders()
    assert set(notifier.notified_handles) == {'John#004', 'Jane#005'}


def test_user_can_re_set_reminder_time(clock, calendar, notifier):
    clock.set_time(datetime(2023, 6, 6, 12, 34, 52))
    event = calendar.add_event('Test event', datetime(2023, 6, 7, 12), 'Alice#003', timedelta(hours=2))
    calendar.declare_joining_event('Bob#002', event.code)
    calendar.set_event_reminder('Alice#003', event.code, timedelta(hours=3))
    clock.set_time(datetime(2023, 6, 7, 9))
    calendar.notify_for_pending_reminders()
    assert set(notifier.notified_handles) == {'Alice#003', 'Bob#002'}


def test_users_are_not_reminded_too_early_when_reminder_is_re_set(clock, calendar, notifier):
    clock.set_time(datetime(2023, 12, 23, 13, 1, 22))
    event = calendar.add_event('Test event', datetime(2023, 12, 24, 12), 'Alice#003', timedelta(hours=3))
    calendar.declare_joining_event('Bob#002', event.code)
    clock.progress(timedelta(hours=3))
    calendar.set_event_reminder('Alice#003', event.code, timedelta(hours=1))
    clock.set_time(datetime(2023, 12, 24, 10, 30))
    calendar.notify_for_pending_reminders()
    assert set(notifier.notified_handles) == set()


def test_cannot_set_reminder_for_non_existent_event(clock, calendar, notifier):
    clock.set_time(datetime(2023, 5, 3, 15, 32, 10))
    with pytest.raises(EventNotFound):
        calendar.set_event_reminder('Admin#001', 'tes-1', timedelta(hours=1))