from datetime import datetime


from eventbot.domain.services.parser.polish import PolishParser
from tests.fakes import FakeClock


def test_event_name_is_parsed_correctly():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Konferencja głosowa o zgłoszeniach na Google Meet, jutro o ósmej trzydzieści pięć po południu')
    assert result.name == 'Konferencja głosowa o zgłoszeniach na Google Meet'


def test_pattern_next_day_with_pm():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Konferencja głosowa na Google Meet. Jutro o ósmej trzydzieści pięć po południu')
    assert result.time == datetime(2023, 8, 11, 20, 35)


def test_pattern_next_day_with_24_clock_format():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Granie w Dotę jutro o 21:37')
    assert result.time == datetime(2023, 8, 11, 21, 37)


def test_pattern_next_week_with_single_numeral_as_hour():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Spotkanie na głosowym za tydzień o 20')
    assert result.time == datetime(2023, 8, 17, 20)


def test_pattern_next_two_days_with_morning():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Telefon pojutrze o 8 rano')
    assert result.time == datetime(2023, 8, 12, 8)


def test_pattern_hour_expressed_as_two_natural_words():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Ważne wydarzenie, jutro o dwudziestej pierwszej')
    assert result.time == datetime(2023, 8, 11, 21)


def test_pattern_hour_and_minutes_expressed_as_two_natural_words():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Ważne wydarzenie, jutro o dwudziestej jeden')
    assert result.time == datetime(2023, 8, 11, 20, 1)


def test_pattern_month_name_full_date():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Spotkanie biznesowe 19 września 2023 o 14')
    assert result.time == datetime(2023, 9, 19, 14)


def test_pattern_explicit_date_dotted_format():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Kurs angielskiego 20.08.2023, 10.30')
    assert result.time == datetime(2023, 8, 20, 10, 30)


def test_pattern_explicit_date_slash_format():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Kurs angielskiego 20/8/2023 10:30')
    assert result.time == datetime(2023, 8, 20, 10, 30)


def test_pattern_month_as_word():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Kurs angielskiego 20 sierpnia 10:30')
    assert result.time == datetime(2023, 8, 20, 10, 30)


def test_pattern_weekday_name():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Impreza w sobotę o dwudziestej pierwszej')
    assert result.time == datetime(2023, 8, 12, 21)


def test_pattern_next_weekday():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Impreza w następną sobotę o 21')
    assert result.time == datetime(2023, 8, 19, 21)


def test_pattern_weekday_next_week():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Impreza w sobotę za tydzień o 21')
    assert result.time == datetime(2023, 8, 19, 21)


def test_pattern_weekday_next_week_reversed():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Impreza za tydzień w sobotę o 21:00')
    assert result.time == datetime(2023, 8, 19, 21)


def test_pattern_weekday_in_count_weeks():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Impreza w sobotę za 2 tygodnie o 21:00')
    assert result.time == datetime(2023, 8, 26, 21)


def test_pattern_weekday_in_count_weeks_reverse():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Impreza o 21:00 za dwa tygodnie w sobotę')
    assert result.time == datetime(2023, 8, 26, 21)


def test_as_many_digits_as_possible():
    parser = PolishParser(FakeClock(datetime(2023, 8, 10)))
    result = parser('Start nocnej zmiany, 31.12.2023 23:45')
    assert result.time == datetime(2023, 12, 31, 23, 45)
