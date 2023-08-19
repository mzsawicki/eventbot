from datetime import datetime

from eventbot.domain import Clock


class LocalTimeClock(Clock):
    def now(self) -> datetime:
        return datetime.now()
