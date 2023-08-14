import abc
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Union
from enum import Enum
from itertools import accumulate

from eventbot.domain.dto import EventParsingResult
from eventbot.domain.ports import Clock
from eventbot.domain.services.parser.parser import Parser
from eventbot.domain.exceptions import ParsingError


class Tag(Enum):
    SEPARATOR = 'separator'

    SCALAR = 'scalar'
    SCALAR_HOUR = 'scalar-hour'
    SCALAR_MINUTE = 'scalar-minute'
    SCALAR_DAY = 'scalar-day'
    SCALAR_MONTH = 'scalar-month'
    SCALAR_YEAR = 'scalar-year'

    POINTER = 'pointer'

    GRABBER = 'grabber'

    REPEATER = 'repeater'
    REPEATER_DAY = 'repeater-day'
    REPEATER_WEEK = 'repeater-week'
    REPEATER_WEEKS = 'repeater-weeks'
    REPEATER_MONTH = 'repeater-month'
    REPEATER_DAY_NAME = 'repeater-day-name'
    REPEATER_MONTH_NAME = 'repeater-month-name'
    REPEATER_TIME = 'repeater-time'
    REPEATER_DAY_PORTION = 'repeater-day-portion'

    ORDINAL = 'ordinal'
    ORDINAL_FEM = 'ordinal-fem'
    ORDINAL_MASC = 'ordinal-masc'
    ORDINAL_DAY = 'ordinal-day'
    ORDINAL_MONTH = 'ordinal-month'
    ORDINAL_HOUR = 'ordinal-hour'

    def __repr__(self):
        return self.value


SEPARATORS = ['at', 'in', 'on']
POINTERS = ['before', 'after']
GRABBERS = ['this', 'next']
GRABBER_THIS = 'this'
GRABBER_NEXT = 'next'
POINTER_PAST = 'before'
POINTER_FUTURE = 'after'


@dataclass
class Token:
    word: str
    tags: List[Tag]

    def __init__(self, word: str):
        self.word: str = word
        self.tags: List = []


def is_separator(word: str) -> bool:
    return word in SEPARATORS


def is_scalar(word: str) -> bool:
    if not word.isnumeric():
        return False
    return any([
        is_scalar_day(word),
        is_scalar_month(word),
        is_scalar_year(word),
        is_scalar_hour(word),
        is_scalar_minute(word),
    ])


def is_scalar_day(word: str) -> bool:
    return 0 < int(word) <= 31


def is_scalar_month(word: str) -> bool:
    return 0 < int(word) <= 12


def is_scalar_year(word: str) -> bool:
    return 2023 <= int(word) <= PolishParser.MAX_YEAR


def is_scalar_hour(word: str) -> bool:
    return int(word) < 24


def is_scalar_minute(word: str) -> bool:
    return int(word) < 60


def is_pointer(word: str) -> bool:
    return word in POINTERS


def is_grabber(word: str) -> bool:
    return word in GRABBERS


def is_repeater(word: str) -> bool:
    return any([
        is_repeater_month(word),
        is_repeater_week(word),
        is_repeater_weeks(word),
        is_repeater_day(word),
        is_repeater_month_name(word),
        is_repeater_day_name(word),
        is_repeater_day_portion(word),
        is_repeater_time(word)
    ])


def is_repeater_month(word: str) -> bool:
    return word == 'month'


def is_repeater_week(word: str) -> bool:
    return word == 'week'


def is_repeater_weeks(word: str) -> bool:
    return word == 'weeks'


def is_repeater_day(word: str) -> bool:
    return word == 'day'


def is_repeater_month_name(word: str) -> bool:
    return word in PolishParser.MONTH_NAMES.values()


def is_repeater_day_name(word: str) -> bool:
    return word in PolishParser.WEEK_DAY_NAMES.values()


def is_repeater_day_portion(word: str) -> bool:
    return word in PolishParser.DAY_PORTION_TERMS.values()


def is_repeater_time(word: str) -> bool:
    return word in PolishParser.TIME_UNITS.values()


def is_ordinal(word: str) -> bool:
    return word in PolishParser.ORDINALS_FEM or word in PolishParser.ORDINALS_MASC


def is_ordinal_fem(word: str) -> bool:
    return word in PolishParser.ORDINALS_FEM


def is_ordinal_masc(word: str) -> bool:
    return word in PolishParser.ORDINALS_MASC


PATTERN_TIME_24_SCALAR = [Tag.SCALAR_HOUR, Tag.SCALAR_MINUTE]
PATTERN_TIME_24_ORDINAL = [Tag.ORDINAL_HOUR, Tag.SCALAR_MINUTE]
PATTERN_TIME_24_SINGLE_SCALAR = [Tag.SEPARATOR, Tag.SCALAR_HOUR]
PATTERN_TIME_24_SINGLE_ORDINAL = [Tag.SEPARATOR, Tag.ORDINAL_HOUR]
PATTERN_TIME_24_SCALAR_TWO_DIGIT_MINUTES = [Tag.SCALAR_HOUR, Tag.SCALAR_MINUTE, Tag.SCALAR_MINUTE]
PATTERN_TIME_24_ORDINAL_TWO_DIGIT_MINUTES = [Tag.ORDINAL_HOUR, Tag.SCALAR_MINUTE, Tag.SCALAR_MINUTE]
PATTERN_TIME_AMPM_SCALAR = [Tag.SCALAR_HOUR, Tag.SCALAR_MINUTE, Tag.REPEATER_DAY_PORTION]
PATTERN_TIME_AMPM_ORDINAL = [Tag.ORDINAL_HOUR, Tag.SCALAR_MINUTE, Tag.REPEATER_DAY_PORTION]
PATTERN_TIME_AMPM_SINGLE_SCALAR = [Tag.SEPARATOR, Tag.SCALAR_HOUR, Tag.REPEATER_DAY_PORTION]
PATTERN_TIME_AMPM_SINGLE_ORDINAL = [Tag.SEPARATOR, Tag.ORDINAL_HOUR, Tag.REPEATER_DAY_PORTION]
PATTERN_TIME_AMPM_SCALAR_TWO_DIGIT_MINUTES = [Tag.SCALAR_HOUR, Tag.SCALAR_MINUTE,
                                              Tag.SCALAR_MINUTE, Tag.REPEATER_DAY_PORTION]
PATTERN_TIME_AMPM_ORDINAL_TWO_DIGIT_MINUTES = [Tag.ORDINAL_HOUR, Tag.SCALAR_MINUTE,
                                               Tag.SCALAR_MINUTE, Tag.REPEATER_DAY_PORTION]

PATTERN_DATE_NEXT_DAY = [Tag.GRABBER, Tag.REPEATER_DAY]
PATTERN_DATE_DAY_AFTER_NEXT_DAY = [Tag.REPEATER_DAY, Tag.POINTER, Tag.GRABBER, Tag.REPEATER_DAY]
PATTERN_DATE_NEXT_WEEK = [Tag.SEPARATOR, Tag.REPEATER_WEEK]
PATTERN_DATE_SCALAR_FULL = [Tag.SCALAR_DAY, Tag.SCALAR_MONTH, Tag.SCALAR_YEAR]
PATTERN_DATE_SCALAR_FULL_REVERSE = [Tag.SCALAR_YEAR, Tag.SCALAR_MONTH, Tag.SCALAR_DAY]
PATTERN_DATE_MONTH_NAME_FULL = [Tag.SCALAR_DAY, Tag.REPEATER_MONTH_NAME, Tag.SCALAR_YEAR]
PATTERN_DATE_ORDINAL = [Tag.ORDINAL_DAY, Tag.REPEATER_MONTH_NAME]
PATTERN_DATE_SCALAR = [Tag.SCALAR_DAY, Tag.REPEATER_MONTH_NAME]
PATTERN_WEEK_DAY = [Tag.REPEATER_DAY_NAME, ]
PATTERN_NEXT_WEEK_DAY = [Tag.GRABBER, Tag.REPEATER_DAY_NAME, ]
PATTERN_WEEK_DAY_IN_WEEK = [Tag.REPEATER_DAY_NAME, Tag.SEPARATOR, Tag.REPEATER_WEEK]
PATTERN_WEEK_DAY_IN_WEEK_REVERSE = [Tag.SEPARATOR, Tag.REPEATER_WEEK, Tag.SEPARATOR, Tag.REPEATER_DAY_NAME]
PATTERN_WEEK_DAY_COUNT_WEEKS = [Tag.REPEATER_DAY_NAME, Tag.SEPARATOR, Tag.SCALAR, Tag.REPEATER_WEEKS]
PATTERN_WEEK_DAY_COUNT_WEEKS_REVERSE = [Tag.SEPARATOR, Tag.SCALAR, Tag.REPEATER_WEEKS,
                                        Tag.SEPARATOR, Tag.REPEATER_DAY_NAME]

AMBIGUOUS_TIME_PATTERNS = {
    'ampm-single-scalar': PATTERN_TIME_AMPM_SINGLE_SCALAR,
    'ampm-single-ordinal': PATTERN_TIME_AMPM_SINGLE_ORDINAL,
    '24-single-scalar': PATTERN_TIME_24_SINGLE_SCALAR,
    '24-single-ordinal': PATTERN_TIME_24_SINGLE_ORDINAL,
}

UNEQUIVOCAL_TIME_PATTERNS = {
    'ampm-ordinal': PATTERN_TIME_AMPM_ORDINAL,
    'ampm-scalar': PATTERN_TIME_AMPM_SCALAR,
    'ampm-ordinal-two-digit-minutes': PATTERN_TIME_AMPM_ORDINAL_TWO_DIGIT_MINUTES,
    'ampm-scalar-two-digit-minutes': PATTERN_TIME_AMPM_SCALAR_TWO_DIGIT_MINUTES,
    '24-ordinal': PATTERN_TIME_24_ORDINAL,
    '24-scalar': PATTERN_TIME_24_SCALAR,
    '24-scalar-two-digit-minutes': PATTERN_TIME_24_SCALAR_TWO_DIGIT_MINUTES,
    '24-ordinal-two-digit-minutes': PATTERN_TIME_24_ORDINAL_TWO_DIGIT_MINUTES,

}

UNEQUIVOCAL_DATE_PATTERNS = {
    'day-after-next-day': PATTERN_DATE_DAY_AFTER_NEXT_DAY,
    'scalar-full': PATTERN_DATE_SCALAR_FULL,
    'scalar-full-reverse': PATTERN_DATE_SCALAR_FULL_REVERSE,
    'month-name-full': PATTERN_DATE_MONTH_NAME_FULL,
    'next-week-day': PATTERN_NEXT_WEEK_DAY,
    'week-day-next-week': PATTERN_WEEK_DAY_IN_WEEK,
    'week-day-next-week-reverse': PATTERN_WEEK_DAY_IN_WEEK_REVERSE,
    'week-day-count-weeks': PATTERN_WEEK_DAY_COUNT_WEEKS,
    'week-day-count-weeks-reverse': PATTERN_WEEK_DAY_COUNT_WEEKS_REVERSE,
}

AMBIGUOUS_DATE_PATTERNS = {
    'next-day': PATTERN_DATE_NEXT_DAY,
    'scalar': PATTERN_DATE_SCALAR,
    'ordinal': PATTERN_DATE_ORDINAL,
    'week-day': PATTERN_WEEK_DAY,
    'next-week': PATTERN_DATE_NEXT_WEEK,
}


def parse_pattern_24(now: datetime, tokens: List[Token]) -> timedelta:
    hour_token, minutes_token = tokens
    hour = int(hour_token.word)
    minutes = int(minutes_token.word)
    return timedelta(hours=hour, minutes=minutes)


def parse_pattern_24_single_scalar(now: datetime, tokens: List[Token]) -> timedelta:
    _, hour_token = tokens
    hour = int(hour_token.word)
    return timedelta(hours=hour)


def parse_pattern_ampm(now: datetime, tokens: List[Token]) -> timedelta:
    hour_token, minutes_token, day_portion = tokens
    hour = int(hour_token.word)
    minutes = int(minutes_token.word)
    if day_portion.word == 'pm':
        hour += 12
    return timedelta(hours=hour, minutes=minutes)


def parse_pattern_ampm_single_scalar(now: datetime, tokens: List[Token]) -> timedelta:
    _, hour_token, day_portion = tokens
    hour = int(hour_token.word)
    if day_portion.word == 'pm':
        hour += 12
    return timedelta(hours=hour)


def parse_pattern_ampm_scalar_two_digit_minutes(now: datetime, tokens: List[Token]) -> timedelta:
    hour_token, minutes_1, minutes_2, day_portion = tokens
    hour = int(hour_token.word)
    minutes = int(minutes_1.word) + int(minutes_2.word)
    if day_portion.word == 'pm':
        hour += 12
    return timedelta(hours=hour, minutes=minutes)


def parse_pattern_24_scalar_two_digit_minutes(now: datetime, tokens: List[Token]) -> timedelta:
    hour_token, minutes_1, minutes_2 = tokens
    hour = int(hour_token.word)
    minutes = int(minutes_1.word) + int(minutes_2.word)
    return timedelta(hours=hour, minutes=minutes)


def parse_pattern_date_next_day(now: datetime, tokens: List[Token]) -> date:
    return date(year=now.year, month=now.month, day=now.day) + timedelta(days=1)


def parse_pattern_date_next_week(now: datetime, tokens: List[Token]) -> date:
    return date(year=now.year, month=now.month, day=now.day) + timedelta(days=7)


def parse_pattern_date_scalar_full(now: datetime, tokens: List[Token]) -> date:
    day, month, year = tokens
    return date(year=int(year.word), month=int(month.word), day=int(day.word))


def parse_pattern_date_scalar_reverse(now: datetime, tokens: List[Token]) -> date:
    year, month, day = tokens
    return date(year=int(year.word), month=int(month.word), day=int(day.word))


def parse_pattern_date_day_after_next_day(now: datetime, tokens: List[Token]) -> date:
    _, pointer, grabber, _ = tokens
    days = 0
    if pointer.word == POINTER_FUTURE:
        days += 1
    else:
        days -= 1
    if grabber.word == GRABBER_NEXT:
        days += 1
    return now + timedelta(days=days)


def parse_pattern_date_month_name_full(now: datetime, tokens: List[Token]) -> date:
    day, month_name, year = tokens
    month = PolishParser.MONTHS_TO_NUMBERS[month_name.word]
    return date(year=int(year.word), month=month, day=int(day.word))


def parse_pattern_date_scalar(now: datetime, tokens: List[Token]) -> date:
    day, month_name = tokens
    month = PolishParser.MONTHS_TO_NUMBERS[month_name.word]
    return date(year=now.year, month=int(month), day=int(day.word))


def parse_pattern_week_day(now: datetime, tokens: List[Token]) -> date:
    week_day_name = tokens.pop()
    week_day_number = PolishParser.WEEK_DAY_NUMBERS[week_day_name.word]
    days_delta = week_day_number - now.weekday()
    if days_delta <= 0:
        days_delta += 7
    return now + timedelta(days=days_delta)


def parse_pattern_weekday_next_week(now: datetime, tokens: List[Token]) -> date:
    grabber, week_day_name = tokens
    week_day_number = PolishParser.WEEK_DAY_NUMBERS[week_day_name.word]
    days_delta = week_day_number - now.weekday()
    if days_delta <= 0:
        days_delta += 7
    if grabber.word == 'next':
        days_delta += 7
    return now + timedelta(days=days_delta)


def parse_pattern_week_day_in_week(now: datetime, tokens: List[Token]) -> date:
    day_name, _, _ = tokens
    week_day_number = PolishParser.WEEK_DAY_NUMBERS[day_name.word]
    days_delta = week_day_number - now.weekday()
    if days_delta <= 0:
        days_delta += 7
    days_delta += 7
    return now.date() + timedelta(days=days_delta)


def parse_pattern_week_day_in_week_reverse(now: datetime, tokens: List[Token]) -> date:
    _, _, _, day_name = tokens
    week_day_number = PolishParser.WEEK_DAY_NUMBERS[day_name.word]
    days_delta = week_day_number - now.weekday()
    if days_delta <= 0:
        days_delta += 7
    days_delta += 7
    return now.date() + timedelta(days=days_delta)


def parse_pattern_week_day_count_weeks(now: datetime, tokens: List[Token]) -> date:
    day_name, _, count, _ = tokens
    week_day_number = PolishParser.WEEK_DAY_NUMBERS[day_name.word]
    days_delta = week_day_number - now.weekday()
    if days_delta <= 0:
        days_delta += 7
    days_delta += int(count.word) * 7
    return now.date() + timedelta(days=days_delta)


def parse_pattern_week_day_count_weeks_reverse(now: datetime, tokens: List[Token]) -> date:
    _, count, _, _, day_name = tokens
    week_day_number = PolishParser.WEEK_DAY_NUMBERS[day_name.word]
    days_delta = week_day_number - now.weekday()
    if days_delta <= 0:
        days_delta += 7
    days_delta += int(count.word) * 7
    return now.date() + timedelta(days=days_delta)


HANDLERS = {
    'ampm-scalar': parse_pattern_ampm,
    'ampm-ordinal': parse_pattern_ampm,
    'ampm-single-scalar': parse_pattern_ampm_single_scalar,
    'ampm-single-ordinal': parse_pattern_ampm_single_scalar,
    'ampm-scalar-two-digit-minutes': parse_pattern_ampm_scalar_two_digit_minutes,
    'ampm-ordinal-two-digit-minutes': parse_pattern_ampm_scalar_two_digit_minutes,
    '24-ordinal': parse_pattern_24,
    '24-scalar': parse_pattern_24,
    '24-single-scalar': parse_pattern_24_single_scalar,
    '24-single-ordinal': parse_pattern_24_single_scalar,
    '24-scalar-two-digit-minutes': parse_pattern_24_scalar_two_digit_minutes,
    '24-ordinal-two-digit-minutes': parse_pattern_24_scalar_two_digit_minutes,
    'next-day': parse_pattern_date_next_day,
    'next-week': parse_pattern_date_next_week,
    'day-after-next-day': parse_pattern_date_day_after_next_day,
    'scalar-full': parse_pattern_date_scalar_full,
    'ordinal-full': parse_pattern_date_scalar_full,
    'scalar-full-reverse': parse_pattern_date_scalar_reverse,
    'month-name-full': parse_pattern_date_month_name_full,
    'scalar': parse_pattern_date_scalar,
    'ordinal': parse_pattern_date_scalar,
    'week-day': parse_pattern_week_day,
    'next-week-day': parse_pattern_weekday_next_week,
    'week-day-next-week': parse_pattern_week_day_in_week,
    'week-day-next-week-reverse': parse_pattern_week_day_in_week_reverse,
    'week-day-count-weeks': parse_pattern_week_day_count_weeks,
    'week-day-count-weeks-reverse': parse_pattern_week_day_count_weeks_reverse,
}


def match_pattern(pattern: List[Tag], tokens: List[Token]) -> bool:
    for tag, token in zip(pattern, tokens):
        if tag not in token.tags:
            return False
    return True


class Reducer(metaclass=abc.ABCMeta):
    def __init__(self, token1: Token, token2: Token):
        self._token1 = token1
        self._token2 = token2

    @abc.abstractmethod
    def match(self) -> bool:
        raise NotImplemented

    @abc.abstractmethod
    def reduce(self) -> Token:
        raise NotImplemented


class DayPortionReducer(Reducer):
    def match(self) -> bool:
        return Tag.POINTER in self._token1.tags and Tag.REPEATER_DAY_PORTION in self._token2.tags

    def reduce(self) -> Token:
        if self._token1.word == 'before' and self._token2.word == 'noon':
            token = Token('am')
            token.tags.append(Tag.REPEATER_DAY_PORTION)
            return token
        elif self._token1.word == 'after' and self._token2.word == 'noon':
            token = Token('pm')
            token.tags.append(Tag.REPEATER_DAY_PORTION)
            return token
        else:
            return self._token2


class NoTagReducer(Reducer):
    def match(self) -> bool:
        return not self._token1.tags and not self._token2.tags

    def reduce(self) -> Token:
        return Token(' '.join((self._token1.word, self._token2.word)))


class SeparatorNoTagReducer(Reducer):
    def match(self) -> bool:
        return Tag.SEPARATOR in self._token1.tags and not self._token2.tags

    def reduce(self) -> Token:
        return Token(' '.join((self._token1.word, self._token2.word)))


class MascOrdinalReducer(Reducer):
    def match(self) -> bool:
        return Tag.ORDINAL_MASC in self._token1.tags and Tag.ORDINAL_MASC in self._token2.tags \
               and self._decimal_part_detected() and self._unit_part_detected()

    def reduce(self) -> Token:
        token_1_value = int(self._token1.word)
        token_2_value = int(self._token2.word)
        reduced_value = token_1_value + token_2_value
        token = Token(str(reduced_value))
        token.tags.append(Tag.ORDINAL)
        token.tags.append(Tag.ORDINAL_MASC)
        if 0 < reduced_value <= 31:
            token.tags.append(Tag.ORDINAL_DAY)
        if 0 < reduced_value <= 12:
            token.tags.append(Tag.ORDINAL_MONTH)
        return token

    def _decimal_part_detected(self) -> bool:
        return int(self._token1.word) in [20, 30]

    def _unit_part_detected(self) -> bool:
        return 0 < int(self._token2.word) < 10


class FemOrdinalReducer(Reducer):
    def match(self) -> bool:
        return Tag.ORDINAL_FEM in self._token1.tags and Tag.ORDINAL_FEM in self._token2.tags \
               and self._decimal_part_detected() and self._unit_part_detected()

    def reduce(self) -> Token:
        token_1_value = int(self._token1.word)
        token_2_value = int(self._token2.word)
        reduced_value = token_1_value + token_2_value
        token = Token(str(reduced_value))
        token.tags.append(Tag.ORDINAL)
        token.tags.append(Tag.ORDINAL_FEM)
        if 0 < reduced_value <= 23:
            token.tags.append(Tag.ORDINAL_HOUR)
        return token

    def _decimal_part_detected(self) -> bool:
        return int(self._token1.word) in [20, 30]

    def _unit_part_detected(self) -> bool:
        return 0 < int(self._token2.word) < 10


class PolishParser(Parser):
    MAX_YEAR = 2030
    SCALARS = {
        'jeden': '1',
        'dwa': '2',
        'trzy': '3',
        'cztery': '4',
        'piec': '5',
        'szesc': '6',
        'siedem': '7',
        'osiem': '8',
        'dziewiec': '9',
        'dziesieć': '10',
        'jedenascie': '11',
        'dwanascie': '12',
        'trzynascie': '13',
        'czternascie': '14',
        'pietnascie': '15',
        'szesnascie': '16',
        'siedemnascie': '17',
        'osiemnascie': '18',
        'dziewietnaście': '19',
        'dwadziescia': '20',
        'trzydziesci': '30',
        'czterdziesci': '40',
        'piecdziesiąt': '50',
        '00': '0',
        '01': '1',
        '02': '2',
        '03': '3',
        '04': '4',
        '05': '5',
        '06': '6',
        '07': '7',
        '08': '8',
        '09': '9'
    }

    ORDINALS_FEM = {
        'pierwsza': '1',
        'pierwszej': '1',
        'druga': '2',
        'drugiej': '2',
        'trzecia': '3',
        'trzeciej': '3',
        'czwarta': '4',
        'czwartej': '4',
        'piata': '5',
        'piatej': '5',
        'szosta': '6',
        'szostej': '6',
        'siodma': '7',
        'siodmej': '7',
        'osma': '8',
        'osmej': '8',
        'dziewiata': '9',
        'dziewiatej': '9',
        'dziesiata': '10',
        'dziesiatej': '10',
        'jedenasta': '11',
        'jedenastej': '11',
        'dwunasta': '12',
        'dwunastej': '12',
        'trzynasta': '13',
        'trzynastej': '13',
        'czternasta': '14',
        'czternastej': '14',
        'pietnasta': '15',
        'pietnastej': '15',
        'szesnasta': '16',
        'szesnastej': '16',
        'siedemnasta': '17',
        'siedemnastej': '17',
        'osiemnasta': '18',
        'osiemnastej': '18',
        'dziewietnasta': '19',
        'dziewietnastej': '19',
        'dwudziesta': '20',
        'dwudziestej': '20',
    }

    ORDINALS_MASC = {
        'pierwszy': '1',
        'pierwszego': '1',
        'drugi': '2',
        'drugiego': '2',
        'trzeci': '3',
        'trzeciego': '3',
        'czwarty': '4',
        'czwartego': '4',
        'piaty': '5',
        'piatego': '5',
        'szosty': '6',
        'szostego': '6',
        'siodmy': '7',
        'siodmego': '7',
        'osmy': '8',
        'osmego': '8',
        'dziewiaty': '9',
        'dziewiatego': '9',
        'dziesiaty': '10',
        'dziesiatego': '10',
        'jedenasty': '11',
        'jedenastego': '11',
        'dwunasty': '12',
        'dwunastego': '12',
        'trzynasty': '13',
        'czternasty': '14',
        'czternastego': '14',
        'pietnasty': '15',
        'pietnastego': '15',
        'szesnasty': '16',
        'szesnastego': '16',
        'siedemnasty': '17',
        'siedemnastego': '17',
        'osiemnasty': '18',
        'osiemnastego': '18',
        'dziewietnasty': '19',
        'dziewietnastego': '19',
        'dwudziesty': '20',
        'dwudziestego': '20',
        'trzydziesty': '30',
        'trzydziestego': '30',
    }

    TIME_RELATION_WORDS = {
        'za': 'in',
        'o': 'at',
        'w': 'at',
        'na': 'at',
        'po': 'after',
        'nastepny': 'next',
        'nastepnego': 'next',
        'nastepnym': 'next',
        'nastepna': 'next',
        'kolejny': 'next',
        'kolejnego': 'next',
        'kolejnym': 'next',
        'kolejną': 'next',
        'jutro': 'next day',
        'pojutrze': 'day after next day',
        'za tydzien': 'next week',
        'za miesiac': 'next month',
        'przed': 'before',
        'wczesniej': 'before',
        'ten': 'this',
        'tym': 'this',
        'obecny': 'this',
        'obecnym': 'this',
        'biezacy': 'this',
        'biezacym': 'this',
        'biezacego': 'this'
    }

    TIME_UNITS = {
        'minuta': 'minute',
        'minute': 'minute',
        'minuty': 'minutes',
        'godzina': 'hour',
        'godzine': 'hour',
        'godzinie': 'hour',
        'godziny': 'hours',
        'dzien': 'day',
        'dni': 'days',
        'dnia': 'day',
        'tydzien': 'week',
        'tygodnie': 'weeks',
        'miesiac': 'month',
        'miesiace': 'months'
    }

    WEEK_DAY_NAMES = {
        'poniedzialek': 'monday',
        'wtorek': 'tuesday',
        'sroda': 'wednesday',
        'srodę': 'wednesday',
        'czwartek': 'thursday',
        'piatek': 'friday',
        'sobota': 'saturday',
        'sobote': 'saturday',
        'niedziela': 'sunday',
        'niedziele': 'sunday'
    }

    WEEK_DAY_NUMBERS = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }

    MONTH_NAMES = {
        'styczen': 'january',
        'stycznia': 'january',
        'luty': 'february',
        'lutego': 'february',
        'marzec': 'march',
        'marca': 'march',
        'kwiecien': 'april',
        'kwietnia': 'april',
        'maj': 'may',
        'maja': 'may',
        'czerwiec': 'june',
        'czerwca': 'june',
        'lipiec': 'july',
        'lipca': 'july',
        'sierpien': 'august',
        'sierpnia': 'august',
        'wrzesien': 'september',
        'wrzesnia': 'september',
        'pazdziernik': 'october',
        'pazdziernika': 'october',
        'listopad': 'november',
        'listopada': 'november',
        'grudzien': 'december',
        'grudnia': 'december'
    }

    MONTH_ROMAN_NUMBERS = {
        'I': 'january',
        'II': 'february',
        'III': 'march',
        'IV': 'april',
        'V': 'may',
        'VI': 'june',
        'VII': 'july',
        'VIII': 'august',
        'IX': 'september',
        'X': 'october',
        'XI': 'november',
        'XII': 'december'
    }

    DAY_PORTION_TERMS = {
        'rano': 'am',
        'wieczorem': 'pm',
        'poludnie': 'noon',
        'poludniu': 'noon'
    }

    REMIND_WORD = 'remind'

    REMIND_SYNONYMS = [
        'powiadom',
        'powiadomic',
        'powiadomiony',
        'powiadomieni',
        'zawiadom',
        'zawiadomic',
        'zawiadomiony',
        'zawiadomieni',
        'przypomnienie',
        'przypomniec',
        'przypomnij'
    ]

    COMMAND_SYNONYMS = {
        'dodaj',
        'utworz',
        'stworz',
        'ustaw'
    }

    POLISH_DIACRITICS = {
        'ą': 'a',
        'ć': 'c',
        'ę': 'e',
        'ł': 'l',
        'ń': 'n',
        'ś': 's',
        'ó': 'o',
        'ź': 'z',
        'ż': 'z'
    }

    MONTHS_TO_NUMBERS = {
        'january': 1,
        'february': 2,
        'march': 3,
        'april': 4,
        'may': 5,
        'june': 6,
        'july': 7,
        'august': 8,
        'september': 9,
        'october': 10,
        'november': 11,
        'december': 12
    }

    def __init__(self, clock: Clock):
        self._now = clock.now()

    def __call__(self, text: str) -> EventParsingResult:
        normalized_text = PolishParser._normalize(text)
        tokens = PolishParser._tokenize(normalized_text)
        reduced_tokens = PolishParser._reduce(tokens)
        tagged_tokens = [token for token in reduced_tokens if token.tags]
        date_, remaining_tokens = self._seek_date_unequivocal(tagged_tokens)
        time, remaining_tokens = self._seek_time_unequivocal(remaining_tokens)
        if not date_:
            date_, remaining_tokens = self._seek_date_ambiguous(remaining_tokens)
        if not time:
            time, remaining_tokens = self._seek_time_ambiguous(remaining_tokens)
        if not date_ or not time:
            raise ParsingError(text)
        datetime_ = datetime(year=date_.year, month=date_.month, day=date_.day) + time
        untagged_tokens = [token for token in reduced_tokens if not token.tags]
        event_name = self._seek_name(untagged_tokens, text)
        return EventParsingResult(event_name, datetime_)

    def _seek_time_unequivocal(self, tokens: List[Token]) -> (Optional[timedelta], List[Token]):
        return self._parse(tokens, UNEQUIVOCAL_TIME_PATTERNS)

    def _seek_time_ambiguous(self, tokens: List[Token]) -> (Optional[timedelta], List[Token]):
        return self._parse(tokens, AMBIGUOUS_TIME_PATTERNS)

    def _seek_date_unequivocal(self, tokens: List[Token]) -> (Optional[date], List[Token]):
        return self._parse(tokens, UNEQUIVOCAL_DATE_PATTERNS)

    def _seek_date_ambiguous(self, tokens: List[Token]) -> (Optional[date], List[Token]):
        return self._parse(tokens, AMBIGUOUS_DATE_PATTERNS)

    def _seek_name(self, untagged_tokens: List[Token], original_text: str) -> str:
        original_text_words = original_text.split(' ')
        for token in untagged_tokens:
            for chain in list(accumulate(original_text_words, func=lambda x, y: ' '.join((x, y)))):
                if token.word == PolishParser._normalize(chain).strip():
                    return remove_training_specials(chain)
        raise ParsingError(original_text)

    def _parse(self, tokens: List[Token], patterns: Dict[str, List[Tag]]) \
            -> (Optional[Union[date, timedelta]], List[Token]):
        for pattern_name, pattern in patterns.items():
            i = 0
            while i + len(pattern) <= len(tokens):
                tokens_portion = tokens[i:i + len(pattern)]
                if match_pattern(pattern, tokens_portion):
                    remaining_tokens = tokens[:i] + tokens[i + len(pattern):]
                    handler = HANDLERS[pattern_name]
                    time = handler(self._now, tokens_portion)
                    return time, remaining_tokens
                i += 1
        return None, tokens

    @staticmethod
    def _normalize(text: str) -> str:
        lower_text = text.lower()
        # Get rid of all special characters
        lower_text = re.sub(r'\W+', ' ', lower_text)

        words = lower_text.split(' ')
        # Normalize diacritics
        words = [PolishParser._normalize_polish_diacritics(word) for word in words]
        # If first word is a command synonym, remove it
        if words[0] in PolishParser.COMMAND_SYNONYMS:
            words = words[1:]
        # Replace all numbers written as words with digit values
        words = [PolishParser.SCALARS[word] if word in PolishParser.SCALARS
                 else word for word in words]
        # Normalize words related to relative time description
        words = [PolishParser.TIME_RELATION_WORDS[word] if word in PolishParser.TIME_RELATION_WORDS
                 else word for word in words]
        # Normalize time terms
        words = [PolishParser.TIME_UNITS[word] if word in PolishParser.TIME_UNITS
                 else word for word in words]
        # Normalize weekday names
        words = [PolishParser.WEEK_DAY_NAMES[word] if word in PolishParser.WEEK_DAY_NAMES
                 else word for word in words]
        # Normalize 'remind' synonyms
        words = [PolishParser.REMIND_WORD if word in PolishParser.REMIND_SYNONYMS
                 else word for word in words]
        # Normalize day portion terms
        words = [PolishParser.DAY_PORTION_TERMS[word] if word in PolishParser.DAY_PORTION_TERMS
                 else word for word in words]
        # Normalize month names
        words = [PolishParser.MONTH_NAMES[word] if word in PolishParser.MONTH_NAMES
                 else word for word in words]
        # Normalize months as roman numbers
        words = [PolishParser.MONTH_ROMAN_NUMBERS[word] if word in PolishParser.MONTH_ROMAN_NUMBERS
                 else word for word in words]
        # Remove 'empty' words
        words = [word for word in words if word != ' ']
        normalized_text = ' '.join(words)
        return normalized_text

    @staticmethod
    def _tokenize(text: str) -> List[Token]:
        tokens = [PolishParser._make_token(word) for word in text.split(' ')]
        return tokens

    @staticmethod
    def _reduce(tokens: List[Token]) -> List[Token]:
        reducer_types = (SeparatorNoTagReducer, NoTagReducer, DayPortionReducer,
                         MascOrdinalReducer, FemOrdinalReducer)
        for reducer_type in reducer_types:
            i = 0
            while i < len(tokens[:-1]):
                reducer = reducer_type(tokens[i], tokens[i+1])
                if reducer.match():
                    new_token = reducer.reduce()
                    tokens.insert(i, new_token)
                    tokens.pop(i+1)
                    tokens.pop(i+1)
                    i -= 1
                i += 1
        return tokens

    @staticmethod
    def _make_token(word: str) -> Token:
        token = Token(word)
        if is_separator(word):
            token.tags.append(Tag.SEPARATOR)
        if is_scalar(word):
            token.tags.append(Tag.SCALAR)
            if is_scalar_month(word):
                token.tags.append(Tag.SCALAR_MONTH)
            if is_scalar_day(word):
                token.tags.append(Tag.SCALAR_DAY)
            if is_scalar_hour(word):
                token.tags.append(Tag.SCALAR_HOUR)
            if is_scalar_minute(word):
                token.tags.append(Tag.SCALAR_MINUTE)
            if is_scalar_year(word):
                token.tags.append(Tag.SCALAR_YEAR)
        if is_pointer(word):
            token.tags.append(Tag.POINTER)
        if is_grabber(word):
            token.tags.append(Tag.GRABBER)
        if is_repeater(word):
            token.tags.append(Tag.REPEATER)
            if is_repeater_month(word):
                token.tags.append(Tag.REPEATER_MONTH)
            if is_repeater_week(word):
                token.tags.append(Tag.REPEATER_WEEK)
            if is_repeater_day(word):
                token.tags.append(Tag.REPEATER_DAY)
            if is_repeater_day_portion(word):
                token.tags.append(Tag.REPEATER_DAY_PORTION)
            if is_repeater_month_name(word):
                token.tags.append(Tag.REPEATER_MONTH_NAME)
            if is_repeater_day_name(word):
                token.tags.append(Tag.REPEATER_DAY_NAME)
            if is_repeater_time(word):
                token.tags.append(Tag.REPEATER_TIME)
            if is_repeater_weeks(word):
                token.tags.append(Tag.REPEATER_WEEKS)
        if is_ordinal(word):
            token.tags.append(Tag.ORDINAL)
            if is_ordinal_fem(word):
                token = fem_ordinal_word_to_number(token)
                token.tags.append(Tag.ORDINAL_FEM)
                if is_scalar_hour(token.word):
                    token.tags.append(Tag.ORDINAL_HOUR)
            if is_ordinal_masc(word):
                token = masc_ordinal_word_to_number(token)
                token.tags.append(Tag.ORDINAL_MASC)
                if is_scalar_day(token.word):
                    token.tags.append(Tag.ORDINAL_DAY)
                if is_scalar_month(token.word):
                    token.tags.append(Tag.ORDINAL_MONTH)
        return token

    @staticmethod
    def _normalize_polish_diacritics(word: str) -> str:
        for diacritic, normalized in PolishParser.POLISH_DIACRITICS.items():
            word = word.replace(diacritic, normalized)
        return word


def remove_training_specials(text: str) -> str:
    trailing_char = text[-1]
    if not trailing_char.isalnum():
        return text[:-1]
    return text


def fem_ordinal_word_to_number(token: Token) -> Token:
    token.word = PolishParser.ORDINALS_FEM[token.word]
    return token


def masc_ordinal_word_to_number(token: Token) -> Token:
    token.word = PolishParser.ORDINALS_MASC[token.word]
    return token
