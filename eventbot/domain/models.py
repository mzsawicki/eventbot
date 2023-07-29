import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass

from eventbot.domain import vo
from eventbot.domain import enums
from eventbot.domain import ports


class User:
    def __init__(self, handle: str, is_admin: bool = False, event_creation_enabled: bool = True):
        self._id: uuid.UUID = uuid.uuid4()
        self._handle: str = handle
        self._is_admin: bool = is_admin
        self._event_creation_enabled: bool = event_creation_enabled

    def __eq__(self, other: 'User'):
        return self._id == other._id

    @property
    def handle(self) -> str:
        return self._handle

    @property
    def is_permitted_to_create_events(self) -> bool:
        return self._event_creation_enabled

    @property
    def is_admin(self) -> bool:
        return self._is_admin


@dataclass(init=True, frozen=True)
class EventEntry:
    MIN_NAME_LEN = 3

    name: str
    code: vo.EventCode
    time: datetime
    owner: User
    id: uuid.UUID = uuid.uuid4()

    def is_owner(self, user: User) -> bool:
        return user == self.owner

    def __eq__(self, other: 'EventEntry'):
        return self.id == other.id


@dataclass(init=True, frozen=True)
class EventAttendanceDeclaration:
    user: User
    event: EventEntry
    decision: enums.EventAttendanceDecision
    id: uuid.UUID = uuid.uuid4()

    @property
    def is_positive(self) -> bool:
        return self.decision in [enums.EventAttendanceDecision.YES, enums.EventAttendanceDecision.MAYBE]


class EventReminder:
    def __init__(self, event: EventEntry, remind_time_before: timedelta):
        self._id: uuid.UUID = uuid.uuid4()
        self._event: EventEntry = event
        self._remind_at: datetime = self._calculate_remind_at(remind_time_before)

    @property
    def event(self) -> EventEntry:
        return self._event

    def time_until(self, clock: ports.Clock) -> timedelta:
        return self._remind_at - clock.now()

    def set_reminder_time(self, remind_time_before: timedelta) -> None:
        self._remind_at = self._calculate_remind_at(remind_time_before)

    def _calculate_remind_at(self, remind_time_before: timedelta) -> datetime:
        return self._event.time - remind_time_before
