from typing import List

from sqlalchemy.orm import Session

from eventbot.domain import Calendar, CalendarRepository, EventReadModel
from eventbot.infrastructure.persistence.tables import event_table, calendar_table


class SQLCalendarRepository(CalendarRepository):
    def __init__(self, session: Session):
        self._session = session

    def does_calendar_exist(self, guild_handle: str, channel_handle: str) -> bool:
        return self._session.query(
                self._session.query(Calendar._id)
                .filter_by(_guild_handle=guild_handle)
                .filter_by(_channel_handle=channel_handle)
                .exists()
            ).scalar()

    def get_calendar_by_guild_and_channel(self, guild_handle: str, channel_handle: str) -> Calendar:
        return self._session.query(Calendar)\
            .with_for_update()\
            .filter_by(_guild_handle=guild_handle)\
            .filter_by(_channel_handle=channel_handle)\
            .one()

    def add_calendar(self, calendar: Calendar) -> None:
        self._session.add(calendar)

    def get_incoming_events(self, guild_handle: str, channel_handle: str) -> List[EventReadModel]:
        records = self._session.query(
            event_table.c._name,
            event_table.c._code,
            event_table.c._time,
            event_table.c._remind_at
        ).join(calendar_table)\
            .filter(calendar_table.c._guild_handle == guild_handle)\
            .filter(calendar_table.c._channel_handle == channel_handle)\
            .all()
        read_models = [EventReadModel(*record) for record in records]
        return read_models
