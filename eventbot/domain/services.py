from datetime import datetime

from eventbot.domain import ports, vo


def create_code_for_event(event_name: str, sequence_generator: ports.EventSequenceGenerator) -> vo.EventCode:
    alpha_part = event_name.lower()[:3]
    numeral_part = next(sequence_generator())
    code = vo.EventCode(f'{alpha_part}-{numeral_part}')
    return code


def create_message_for_event_start_notification(event_name: str, event_code: str) -> str:
    return f'Event {event_name} ({event_code}) is starting!'


def create_message_for_event_reminder_notification(event_name: str, event_code: str, event_time: datetime) -> str:
    return f'Event {event_name} ({event_code}) starts at {event_time}'