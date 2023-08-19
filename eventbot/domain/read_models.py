from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, init=True)
class EventReadModel:
    name: str
    code: str
    time: datetime
    remind_at: datetime
