from eventbot.domain.ports import EventSequenceGenerator
from eventbot.domain.vo import EventCode


class EventCodeProvider:
    def __init__(self, generator: EventSequenceGenerator):
        self._generator = generator

    def __call__(self, event_name: str) -> EventCode:
        alpha_part = event_name.lower()[:3]
        numeral_part = next(self._generator())
        code = EventCode(f'{alpha_part}-{numeral_part}')
        return code
