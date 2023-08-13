import abc

from eventbot.domain.dto import EventParsingResult


class Parser(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self, text: str) -> EventParsingResult:
        raise NotImplemented
