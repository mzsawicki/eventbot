from sqlalchemy import Table, Column, String, ForeignKey, UUID, DateTime,\
    Engine, types, Enum, Integer, Boolean, and_, Sequence
from sqlalchemy.orm import registry, relationship, keyfunc_mapping

from eventbot.domain.model import Calendar, Event, Declaration, CalendarLanguage
from eventbot.domain.vo import EventCode
from eventbot.domain.enums import Decision


EVENT_SEQUENCE_NAME = 'event_name_seq'


class EventCodeVO(types.TypeDecorator):
    impl = types.String(8)

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return EventCode(value)


mapper_registry = registry()


calendar_table = Table(
    'calendar',
    mapper_registry.metadata,
    Column('id', UUID, primary_key=True, key='_id'),
    Column('version', Integer, nullable=False, key='_version'),
    Column('guild_handle', String(64), nullable=False, unique=False, key='_guild_handle'),
    Column('channel_handle', String(64), nullable=False, unique=False, key='_channel_handle'),
    Column('language', Enum(CalendarLanguage), nullable=False, key='_language')
)

event_table = Table(
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

declaration_table = Table(
    'declaration',
    mapper_registry.metadata,
    Column('id', UUID, primary_key=True),
    Column('event_id', UUID, ForeignKey('event._id')),
    Column('user_handle', String(64), nullable=False),
    Column('decision', Enum(Decision), nullable=False),
)

event_sequence = Sequence(EVENT_SEQUENCE_NAME, start=1, increment=1, metadata=mapper_registry.metadata)

mapper_registry.map_imperatively(Calendar, calendar_table, properties={
    '_events': relationship(
        Event,
        collection_class=keyfunc_mapping(lambda event: str(event._code)),
        primaryjoin=and_(event_table.c._calendar_id == calendar_table.c._id, event_table.c._removed == False)
    )})
mapper_registry.map_imperatively(Event, event_table, properties={
    '_declarations': relationship(Declaration)
})
mapper_registry.map_imperatively(Declaration, declaration_table)


def map_tables(engine: Engine) -> None:
    mapper_registry.metadata.create_all(bind=engine)


def drop_tables(engine: Engine) -> None:
    mapper_registry.metadata.drop_all(bind=engine)
    event_sequence.drop(bind=engine)
