from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass(init=True, frozen=True)
class EventParsingResult:
    name: str
    time: datetime
    reminder_delta: Optional[timedelta] = None
