from sqlalchemy.orm import Session

from eventbot.domain import Calendar
from eventbot.application import CalendarRepository


class SQLCalendarRepository(CalendarRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_calendar_by_guild_and_channel(self, guild_handle: str, channel_handle: str) -> Calendar:
        return self._session.query(Calendar)\
            .with_for_update()\
            .filter_by(_guild_handle=guild_handle)\
            .filter_by(_channel_handle=channel_handle)\
            .one()

    def add_calendar(self, calendar: Calendar) -> None:
        self._session.add(calendar)
