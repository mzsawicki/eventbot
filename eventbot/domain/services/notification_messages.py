from datetime import datetime


def create_message_for_event_start_notification(event_name: str, event_code: str) -> str:
    return f'Event {event_name} ({event_code}) is starting!'


def create_message_for_event_reminder_notification(event_name: str, event_code: str, event_time: datetime) -> str:
    return f'Reminder: Event "{event_name}" ({event_code}) starts at {event_time}.'


def create_message_for_event_creation_notification(event_name: str, event_code: str,
                                                   event_time: datetime, remind_time: datetime = None) -> str:
    message = f'Event "{event_name}" (code: {event_code}) has been created and will start at: {event_time}.\n'
    if remind_time:
        message += f'Participants will be reminded at {remind_time}.\n'
    message += 'To declare participation, react to this message:\n' \
               'Yes: :white_check_mark:\n' \
               'No: :negative_squared_cross_mark:\n' \
               'Maybe: :grey_question:'
    return message
