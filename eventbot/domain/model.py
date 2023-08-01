from uuid import UUID, uuid4
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass

from eventbot.domain.ports import Clock, Notifier, EventSequenceGenerator
from eventbot.domain.vo import EventCode
from eventbot.domain.enums import Decision
from eventbot.domain.services import (
    create_code_for_event,
    create_message_for_event_start_notification,
    create_message_for_event_reminder_notification
)
from eventbot.domain.exceptions import (
    EventNotFound,
    EventInThePast,
    UserNotPermittedToDeleteEvent,
    UserNotPermittedToSetReminderForEvent
)


class Calendar:
    def __init__(self, guild_handle: str, channel_handle: str):
        self._id: UUID = uuid4()
        self._guild_handle: str = guild_handle
        self._channel_handle: str = channel_handle
        self._events: Dict[str, Event] = {}
        self._version = 0

    def add_event(self, name: str, time: datetime, owner_handle: str,
                  clock: Clock, sequence_generator: EventSequenceGenerator,
                  reminder_time: timedelta = None) -> str:
        if time <= (current_time := clock.now()):
            raise EventInThePast(current_time, time)
        event_code = create_code_for_event(name, sequence_generator)
        event: Event = Event(name, event_code, time, owner_handle)
        event.declare_yes(owner_handle)
        if reminder_time is not None:
            event.set_reminder(reminder_time)
        self._events[str(event_code)] = event
        self._bump_version()
        return str(event_code)

    def delete_event(self, user_handle: str, event_code: str,) -> None:
        if event_code not in self._events:
            raise EventNotFound(event_code)
        event: Event = self._events[event_code]
        event.ensure_user_can_delete(user_handle)
        del self._events[event_code]
        self._bump_version()

    def set_reminder_for_event(self, user_handle: str, event_code: str, remind_time: timedelta) -> None:
        if event_code not in self._events:
            raise EventNotFound(event_code)
        event: Event = self._events[event_code]
        event.ensure_user_can_set_reminder(user_handle)
        event.set_reminder(remind_time)
        self._bump_version()

    def send_pending_notifications(self, clock: Clock, notifier: Notifier) -> None:
        for _, event in self._events.items():
            event.handle_notification(clock, notifier)
        self._bump_version()

    def declare_yes_to_event(self, user_handle: str, event_code: str) -> None:
        if event_code not in self._events:
            raise EventNotFound(event_code)
        event: Event = self._events[event_code]
        event.declare_yes(user_handle)
        self._bump_version()

    def declare_no_to_event(self, user_handle: str, event_code: str) -> None:
        if event_code not in self._events:
            raise EventNotFound(event_code)
        event: Event = self._events[event_code]
        event.declare_no(user_handle)
        self._bump_version()

    def declare_maybe_to_event(self, user_handle: str, event_code: str) -> None:
        if event_code not in self._events:
            raise EventNotFound(event_code)
        event: Event = self._events[event_code]
        event.declare_maybe(user_handle)
        self._bump_version()

    def _bump_version(self) -> None:
        self._version += 1


class Event:
    def __init__(self, name: str, code: EventCode, time: datetime, owner_handle: str):
        self._id = uuid4()
        self._name: str = name
        self._code: EventCode = code
        self._time: datetime = time
        self._owner_handle: str = owner_handle
        self._reminder: Optional[Reminder] = None
        self._declarations: List[Declaration] = []

    def set_reminder(self, remind_delta: timedelta) -> None:
        self._reminder = Reminder(self._id, self._time - remind_delta)

    def handle_notification(self, clock: Clock, notifier: Notifier) -> None:
        handles_to_notify = [declaration.user_handle for declaration in self._declarations if declaration.is_positive]
        if self._is_pending(clock):
            message = create_message_for_event_start_notification(self._name, str(self._code))
            notifier.notify(message, handles_to_notify)
        else:
            message = create_message_for_event_reminder_notification(self._name, str(self._code), self._time)
            self._reminder.remind_if_pending(message, handles_to_notify, clock, notifier)

    def declare_yes(self, user_handle: str) -> None:
        self._declarations.append(Declaration(event_id=self._id, user_handle=user_handle, decision=Decision.YES))

    def declare_no(self, user_handle: str) -> None:
        self._declarations.append(Declaration(event_id=self._id, user_handle=user_handle, decision=Decision.NO))

    def declare_maybe(self, user_handle: str) -> None:
        self._declarations.append(Declaration(event_id=self._id, user_handle=user_handle, decision=Decision.MAYBE))

    def ensure_user_can_delete(self, user_handle: str) -> None:
        if not self._is_user_owner(user_handle):
            raise UserNotPermittedToDeleteEvent(user_handle, str(self._code))

    def ensure_user_can_set_reminder(self, user_handle: str) -> None:
        if not self._is_user_owner(user_handle):
            raise UserNotPermittedToSetReminderForEvent(user_handle, str(self._code))

    def _is_user_owner(self, user_handle: str) -> bool:
        return user_handle == self._owner_handle

    def _is_pending(self, clock: Clock) -> bool:
        return clock.now() >= self._time


class Reminder:
    def __init__(self, event_id: UUID, remind_at: datetime):
        self._id = uuid4()
        self._event_id = event_id
        self._remind_at = remind_at

    def remind_if_pending(self, message: str, user_handles: List[str],
                          clock: Clock, notifier: Notifier) -> None:
        if self._is_pending(clock):
            notifier.notify(message, user_handles)

    def _is_pending(self, clock: Clock) -> bool:
        return clock.now() >= self._remind_at


@dataclass(init=True, frozen=True)
class Declaration:
    event_id: UUID
    user_handle: str
    decision: Decision
    id: UUID = uuid4()

    @property
    def is_positive(self):
        return self.decision in [Decision.YES, Decision.MAYBE]
