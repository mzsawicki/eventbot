class EventCode:
    MIN_LEN = 5

    def __init__(self, value: str):
        EventCode.validate(value)
        self._value = value

    def __str__(self):
        return self._value

    @staticmethod
    def validate(value: str) -> None:
        if len(value) < EventCode.MIN_LEN:
            raise ValueError(f'Event code cannot be shorter than {EventCode.MIN_LEN} characters')
        if value[3] != '-':
            raise ValueError('Invalid event code format. Valid format is two members separated with "-"')
        if not value[4:].isnumeric():
            raise ValueError('Invalid event code format. All characters after "-" should be digits')
