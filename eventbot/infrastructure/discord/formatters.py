from datetime import datetime

from eventbot.domain import EventReadModel


def format_event(event: EventReadModel) -> str:
    return f'{event.name} ({event.code}): {format_time(event.time)}'


def format_time(time: datetime) -> str:
    return f'{time.day}.{time.month:02d}.{time.year}, {time.hour:02d}:{time.minute:02d}'
