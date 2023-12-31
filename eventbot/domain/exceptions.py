from datetime import datetime


class EventInThePast(Exception):
    def __init__(self, now: datetime, requested_time: datetime):
        super().__init__()
        self.now: datetime = now
        self.requested_time: datetime = requested_time


class ReminderInThePast(Exception):
    def __init__(self, now: datetime, requested_time: datetime):
        super().__init__()
        self.now: datetime = now
        self.requested_time: datetime = requested_time


class EventNotFound(Exception):
    def __init__(self, event_code: str):
        super().__init__()
        self.event_code: str = event_code


class UserNotPermittedToDeleteEvent(Exception):
    def __init__(self, user_handle: str, event_code: str):
        super().__init__()
        self.user_handle: str = user_handle
        self.event_code: str = event_code


class UserNotPermittedToSetReminderForEvent(Exception):
    def __init__(self, user_handle: str, event_code: str):
        super().__init__()
        self.user_handle: str = user_handle
        self.event_code: str = event_code


class ParsingError(Exception):
    def __init__(self, text: str):
        super().__init__()
        self.text = text
