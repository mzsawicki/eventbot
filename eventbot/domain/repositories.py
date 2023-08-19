import abc
from typing import List

from eventbot.domain import Calendar
from eventbot.domain.read_models import EventReadModel


class CalendarRepository(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def does_calendar_exist(self, guild_handle: str, channel_handle: str) -> bool:
        raise NotImplemented

    @abc.abstractmethod
    def get_calendar_by_guild_and_channel(self, guild_handle: str, channel_handle: str) -> Calendar:
        raise NotImplemented

    @abc.abstractmethod
    def add_calendar(self, calendar: Calendar) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def get_incoming_events(self, guild_handle: str, channel_handle: str) -> List[EventReadModel]:
        raise NotImplemented
