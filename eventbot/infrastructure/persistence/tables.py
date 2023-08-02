from sqlalchemy import Table, Column, String, ForeignKey, UUID, DateTime, Engine, types, Enum, Integer, Boolean, and_
from sqlalchemy.orm import registry, relationship, keyfunc_mapping

from eventbot.domain.model import Calendar, Event, Declaration
from eventbot.domain.vo import EventCode
from eventbot.domain.enums import Decision


class EventCodeVO(types.TypeDecorator):
    impl = types.String(8)

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return EventCode(value)


def map_tables(engine: Engine) -> None:
    mapper_registry = registry()

    calendar = Table(
        'calendar',
        mapper_registry.metadata,
        Column('id', UUID, primary_key=True, key='_id'),
        Column('version', Integer, nullable=False, key='_version'),
        Column('guild_handle', String(64), nullable=False, unique=True, key='_guild_handle'),
        Column('channel_handle', String(64), nullable=False, unique=True, key='_channel_handle'),
    )

    event = Table(
        'event',
        mapper_registry.metadata,
        Column('id', UUID, primary_key=True, key='_id'),
        Column('calendar_id', UUID, ForeignKey('calendar._id'), key='_calendar_id'),
        Column('name', String(64), nullable=False, key='_name'),
        Column('code', EventCodeVO, nullable=False, unique=True, key='_code'),
        Column('time', DateTime, nullable=False, key='_time'),
        Column('owner_handle', String(64), nullable=False, key='_owner_handle'),
        Column('remind_at', DateTime, nullable=True, key='_remind_at'),
        Column('removed', Boolean, nullable=False, key='_removed'),
        Column('reminded', Boolean, nullable=False, key='_reminded')
    )

    declaration = Table(
        'declaration',
        mapper_registry.metadata,
        Column('id', UUID, primary_key=True),
        Column('event_id', UUID, ForeignKey('event._id')),
        Column('user_handle', String(64), nullable=False),
        Column('decision', Enum(Decision), nullable=False),
    )

    mapper_registry.map_imperatively(Calendar, calendar, properties={
        '_events': relationship(
            Event,
            collection_class=keyfunc_mapping(lambda event: str(event._code)),
            primaryjoin=and_(event.c._calendar_id == calendar.c._id, event.c._removed == False)
        )})
    mapper_registry.map_imperatively(Event, event, properties={
        '_declarations': relationship(Declaration)
    })
    mapper_registry.map_imperatively(Declaration, declaration)

    mapper_registry.metadata.drop_all(bind=engine)
    mapper_registry.metadata.create_all(bind=engine)
