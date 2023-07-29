from datetime import datetime, timedelta
from typing import List, Optional
import uuid
from itertools import filterfalse

from eventbot.domain import exceptions
from eventbot.domain import models
from eventbot.domain import ports
from eventbot.domain import services
from eventbot.domain import enums


class Calendar:
    def __init__(self,
                 channel_name: str,
                 clock: ports.Clock,
                 notifier: ports.EventReminderNotifier,
                 event_code_provider: services.EventCodeProvider):
        self._id: uuid.UUID = uuid.uuid4()
        self._version: int = 0
        self._events: List[models.EventEntry] = []
        self._reminders: List[models.EventReminder] = []
        self._declarations: List[models.EventAttendanceDeclaration] = []
        self._users: List[models.User] = []
        self._channel_name = channel_name
        self._clock = clock
        self._notifier = notifier
        self._get_event_code = event_code_provider

    @property
    def version(self) -> int:
        return self._version

    @property
    def channel_name(self) -> str:
        return self._channel_name

    def add_event(self, name: str, event_time: datetime,
                  owner_handle: str, reminder_time: timedelta = None) -> models.EventEntry:
        owner = self._get_user_by_handle(owner_handle)
        if not owner.is_permitted_to_create_events:
            raise exceptions.UserForbiddenFromCreatingEvents(owner_handle)
        if event_time <= (time_now := self._clock.now()):
            raise exceptions.EventInThePast(time_now, event_time)
        event = models.EventEntry(name=name, code=self._get_event_code(name), time=event_time, owner=owner)
        self._events.append(event)
        if reminder_time:
            reminder = models.EventReminder(event, reminder_time)
            self._reminders.append(reminder)
        owner_declaration = models.EventAttendanceDeclaration(user=owner, event=event,
                                                              decision=enums.EventAttendanceDecision.YES)
        self._declarations.append(owner_declaration)
        self._bump_version()
        return event

    def delete_event(self, issuer_user_handle: str, event_code: str) -> None:
        issuer_user = self._get_user_by_handle(issuer_user_handle)
        event = self._get_event_by_code(event_code)
        if not event.is_owner(issuer_user) and not issuer_user.is_admin:
            raise exceptions.UserNotPermittedToDeleteEvent(issuer_user_handle, event_code)
        self._reminders = list(filterfalse(lambda r: r.event == event, self._reminders))
        self._declarations = list(filterfalse(lambda d: d.event == event, self._declarations))
        self._events.remove(event)
        self._bump_version()

    def add_user(self, handle: str, is_admin: bool = False, event_creation_enabled: bool = True) -> None:
        self._users.append(models.User(handle, is_admin, event_creation_enabled))
        self._bump_version()

    def declare_joining_event(self, user_handle: str, event_code: str) -> None:
        user = self._get_user_by_handle(user_handle)
        event = self._get_event_by_code(event_code)
        declaration = models.EventAttendanceDeclaration(
            user=user, event=event, decision=enums.EventAttendanceDecision.YES)
        self._declarations.append(declaration)
        self._bump_version()

    def declare_uncertain_for_event(self, user_handle: str, event_code: str) -> None:
        user = self._get_user_by_handle(user_handle)
        event = self._get_event_by_code(event_code)
        declaration = models.EventAttendanceDeclaration(
            user=user, event=event, decision=enums.EventAttendanceDecision.MAYBE)
        self._declarations.append(declaration)
        self._bump_version()

    def declare_declined_event(self, user_handle: str, event_code: str) -> None:
        user = self._get_user_by_handle(user_handle)
        event = self._get_event_by_code(event_code)
        declaration = models.EventAttendanceDeclaration(
            user=user, event=event, decision=enums.EventAttendanceDecision.NO)
        self._declarations.append(declaration)
        self._bump_version()

    def set_event_reminder(self, user_handle, event_code: str, reminder_time: timedelta) -> None:
        user = self._get_user_by_handle(user_handle)
        event = self._get_event_by_code(event_code)
        if not event.is_owner(user):
            raise exceptions.UserNotPermittedToSetReminderForEvent(user_handle, event_code)
        if existing_reminder := self._get_existing_event_reminder(event):
            existing_reminder.set_reminder_time(reminder_time)
        else:
            reminder = models.EventReminder(event, reminder_time)
            self._reminders.append(reminder)
        self._bump_version()

    def notify_for_pending_reminders(self) -> None:
        self._sort_reminders()
        pending_reminders = list(filter(lambda r: r.time_until(self._clock) <= timedelta(seconds=0), self._reminders))
        for reminder in pending_reminders:
            event = reminder.event
            yes_or_maybe_declarations = list(filter(lambda d: d.is_positive, self._declarations))
            users_handles_to_notify = [declaration.user.handle for declaration in yes_or_maybe_declarations]
            self._notifier.notify(event.name, event.time, users_handles_to_notify)
        self._reminders = filterfalse(lambda r: r in pending_reminders, self._reminders)
        self._bump_version()

    def _sort_reminders(self) -> None:
        self._reminders.sort(key=lambda r: r.time_until(self._clock))

    def _get_user_by_handle(self, handle: str) -> models.User:
        if user := next((user for user in self._users if user.handle == handle), None):
            return user
        raise exceptions.UserNotFound(handle)

    def _get_event_by_code(self, code: str) -> models.EventEntry:
        if event := next((event for event in self._events if event.code == code), None):
            return event
        raise exceptions.EventNotFound(code)

    def _get_existing_event_reminder(self, event: models.EventEntry) -> Optional[models.EventReminder]:
        return next((reminder for reminder in self._reminders if reminder.event == event), None)

    def _bump_version(self) -> None:
        self._version += 1
