from uuid import UUID, uuid4
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

from eventbot.domain.ports import Clock, Notifier, EventSequenceGenerator
from eventbot.domain.vo import EventCode
from eventbot.domain.enums import Decision
from eventbot.domain.services.create_code_for_event import create_code_for_event
from eventbot.domain.services.parser import Parser, PolishParser
from eventbot.domain.exceptions import (
    EventNotFound,
    EventInThePast,
    UserNotPermittedToDeleteEvent,
    UserNotPermittedToSetReminderForEvent,
    ReminderInThePast
)


class CalendarLanguage(Enum):
    PL = 'pl'


class Calendar:
    def __init__(self, guild_handle: str, channel_handle: str, language: CalendarLanguage = CalendarLanguage.PL):
        self._id: UUID = uuid4()
        self._guild_handle: str = guild_handle
        self._channel_handle: str = channel_handle
        self._language = language
        self._events: Dict[str, Event] = {}
        self._version = 0

    def add_event(self,
                  prompt: str,
                  owner_handle: str,
                  clock: Clock,
                  sequence_generator: EventSequenceGenerator,
                  notifier: Notifier
                  ) -> str:
        parser: Parser = self._get_parser(clock)
        event_parsing_result = parser(prompt)
        name = event_parsing_result.name
        time = event_parsing_result.time
        reminder_delta = event_parsing_result.reminder_delta
        current_time = clock.now()
        if time <= current_time:
            raise EventInThePast(current_time, time)
        event_code = create_code_for_event(name, sequence_generator)
        event: Event = Event(self._id, name, event_code, time, owner_handle)
        event.declare_yes(owner_handle)
        if reminder_delta is not None:
            reminder_time = time - reminder_delta
            if reminder_time <= current_time:
                raise ReminderInThePast(current_time, reminder_time)
            event.set_reminder(reminder_delta)
            notifier.notify_event_created(name, str(event_code), time, owner_handle, reminder_time)
        else:
            notifier.notify_event_created(name, str(event_code), time, owner_handle)
        self._events[str(event_code)] = event
        self._bump_version()
        return str(event_code)

    def delete_event(self, user_handle: str, event_code: str) -> None:
        if event_code not in self._events:
            raise EventNotFound(event_code)
        event: Event = self._events[event_code]
        event.ensure_user_can_delete(user_handle)
        event.remove()
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

    def _get_parser(self, clock: Clock):
        if self._language == CalendarLanguage.PL:
            return PolishParser(clock)

    def _bump_version(self) -> None:
        self._version += 1


class Event:
    def __init__(self, calendar_id: UUID, name: str, code: EventCode, time: datetime, owner_handle: str):
        self._id = uuid4()
        self._calendar_id: UUID = calendar_id
        self._name: str = name
        self._code: EventCode = code
        self._time: datetime = time
        self._owner_handle: str = owner_handle
        self._remind_at: Optional[datetime] = None
        self._declarations: List[Declaration] = []
        self._removed: bool = False
        self._reminded: bool = False

    def set_reminder(self, remind_delta: timedelta) -> None:
        self._remind_at = self._time - remind_delta

    def handle_notification(self, clock: Clock, notifier: Notifier) -> None:
        handles_to_notify = [declaration.user_handle for declaration in self._declarations if declaration.is_positive]
        if self._is_pending(clock):
            notifier.notify_event_start(self._name, str(self._code), handles_to_notify)
            self.remove()
        elif self._is_to_remind(clock):
            notifier.notify_reminder(self._name, str(self._code), self._time, handles_to_notify)
            self._mark_as_reminded()

    def declare_yes(self, user_handle: str) -> None:
        if existing_declaration := self._get_existing_declaration(user_handle):
            existing_declaration.decision = Decision.YES
        else:
            self._declarations.append(Declaration(event_id=self._id, user_handle=user_handle, decision=Decision.YES))

    def declare_no(self, user_handle: str) -> None:
        if existing_declaration := self._get_existing_declaration(user_handle):
            existing_declaration.decision = Decision.NO
        else:
            self._declarations.append(Declaration(event_id=self._id, user_handle=user_handle, decision=Decision.NO))

    def declare_maybe(self, user_handle: str) -> None:
        if existing_declaration := self._get_existing_declaration(user_handle):
            existing_declaration.decision = Decision.MAYBE
        else:
            self._declarations.append(Declaration(event_id=self._id, user_handle=user_handle, decision=Decision.MAYBE))

    def ensure_user_can_delete(self, user_handle: str) -> None:
        if not self._is_user_owner(user_handle):
            raise UserNotPermittedToDeleteEvent(user_handle, str(self._code))

    def ensure_user_can_set_reminder(self, user_handle: str) -> None:
        if not self._is_user_owner(user_handle):
            raise UserNotPermittedToSetReminderForEvent(user_handle, str(self._code))

    def remove(self) -> None:
        self._removed = True

    def _mark_as_reminded(self) -> None:
        self._reminded = True

    def _is_user_owner(self, user_handle: str) -> bool:
        return user_handle == self._owner_handle

    def _is_pending(self, clock: Clock) -> bool:
        return not self._removed and clock.now() >= self._time

    def _is_to_remind(self, clock: Clock) -> bool:
        if not self._remind_at or self._reminded:
            return False
        return clock.now() >= self._remind_at

    def _get_existing_declaration(self, user_handle: str) -> Optional['Declaration']:
        return next(
            (declaration for declaration in self._declarations if declaration.user_handle == user_handle),
            None
        )


@dataclass
class Declaration:
    id: UUID
    event_id: UUID
    user_handle: str
    decision: Decision

    def __init__(self, event_id: UUID, user_handle: str, decision: Decision):
        self.id = uuid4()
        self.event_id = event_id
        self.user_handle = user_handle
        self.decision = decision

    @property
    def is_positive(self):
        return self.decision in [Decision.YES, Decision.MAYBE]
