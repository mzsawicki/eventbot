import abc

from eventbot.domain import Calendar


class CalendarRepository(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_calendar_by_guild_and_channel(self, guild_handle: str, channel_handle: str) -> Calendar:
        raise NotImplemented

    @abc.abstractmethod
    def add_calendar(self, calendar: Calendar) -> None:
        raise NotImplemented
