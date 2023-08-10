from datetime import datetime

import pytest


from eventbot.domain.services.parser import PolishParser
from eventbot.domain.dto import EventParsingResult
from tests.fakes import FakeClock


def test_time_parsing_for_basic_example():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Konferencja głosowa na Google Meet. Jutro o ósmej trzydzieści pięć po południu')
    assert result.time == datetime(2023, 8, 11, 20, 35)
