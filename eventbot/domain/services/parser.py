import abc
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Union
from enum import Enum

from eventbot.domain.dto import EventParsingResult
from eventbot.domain.ports import Clock
from eventbot.domain.services.time import next_month


class Parser(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self, text: str) -> EventParsingResult:
        raise NotImplemented


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
    REPEATER_MONTH = 'repeater-month'
    REPEATER_DAY_NAME = 'repeater-day-name'
    REPEATER_MONTH_NAME = 'repeater-month-name'
    REPEATER_TIME = 'repeater-time'
    REPEATER_DAY_PORTION = 'repeater-day-portion'

    def __repr__(self):
        return self.value


SEPARATORS = ['at', 'in', 'on']
POINTERS = ['before', 'after']
GRABBERS = ['this', 'next']
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
    return 2023 < int(word) <= PolishParser.MAX_YEAR


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


PATTERN_TIME_LONG_24 = [Tag.SCALAR_HOUR, Tag.SCALAR_MINUTE, Tag.SCALAR_MINUTE]
PATTERN_TIME_SHORT_24 = [Tag.SCALAR_HOUR, Tag.SCALAR_MINUTE]
PATTERN_TIME_LONG_AMPM = [Tag.SCALAR_HOUR, Tag.SCALAR_MINUTE, Tag.SCALAR_MINUTE, Tag.REPEATER_DAY_PORTION]
PATTERN_TIME_SHORT_AMPM = [Tag.SCALAR_HOUR, Tag.SCALAR_MINUTE, Tag.REPEATER_DAY_PORTION]

PATTERN_DATE_NEXT_DAY = [Tag.GRABBER, Tag.REPEATER_DAY]

AMBIGUOUS_TIME_PATTERNS = [
    PATTERN_TIME_LONG_24,
    PATTERN_TIME_SHORT_24,
]

UNEQUIVOCAL_TIME_PATTERNS = {
    'long-ampm': PATTERN_TIME_LONG_AMPM,
    'short-ampm': PATTERN_TIME_SHORT_AMPM,
}

UNEQUIVOCAL_DATE_PATTERNS = {
    'next-day': PATTERN_DATE_NEXT_DAY,
}


def match_pattern(pattern: List[Tag], tokens: List[Token]) -> bool:
    for tag, token in zip(pattern, tokens):
        if tag not in token.tags:
            return False
    return True


def parse_pattern_time_long_ampm(now: datetime, tokens: List[Token]) -> timedelta:
    hour_token, minutes_dec_token, minutes_token, day_portion_token = tokens
    hour = int(hour_token.word)
    if day_portion_token.word == 'pm':
        hour += 12
    minutes = int(minutes_dec_token.word) + int(minutes_token.word)
    return timedelta(hours=hour, minutes=minutes)


def parse_pattern_date_next_day(now: datetime, tokens: List[Token]) -> date:
    return date(year=now.year, month=now.month, day=now.day) + timedelta(days=1)


HANDLERS = {
    'long-ampm': parse_pattern_time_long_ampm,
    'next-day': parse_pattern_date_next_day
}


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


class PolishParser(Parser):
    MAX_YEAR = 2030
    NUMBERS_AS_WORDS = {
        'jeden': '1',
        'pierwsza': '1',
        'pierwszej': '1',
        'pierwszy': '1',
        'pierwszego': '1',
        'dwa': '2',
        'druga': '2',
        'drugiej': '2',
        'drugi': '2',
        'drugiego': '2',
        'trzy': '3',
        'trzecia': '3',
        'trzeciej': '3',
        'trzeci': '3',
        'trzeciego': '3',
        'cztery': '4',
        'czwarta': '4',
        'czwartej': '4',
        'czwarty': '4',
        'czwartego': '4',
        'piec': '5',
        'piata': '5',
        'piatej': '5',
        'piaty': '5',
        'piatego': '5',
        'szsc': '6',
        'szosta': '6',
        'szostej': '6',
        'szosty': '6',
        'szostego': '6',
        'siedem': '7',
        'siodma': '7',
        'siodmej': '7',
        'siodmy': '7',
        'siodmego': '7',
        'osiem': '8',
        'osma': '8',
        'osmej': '8',
        'osmy': '8',
        'osmego': '8',
        'dziewiec': '9',
        'dziewiata': '9',
        'dziewiatej': '9',
        'dziewiaty': '9',
        'dziewiatego': '9',
        'dziesieć': '10',
        'dziesiata': '10',
        'dziesiatej': '10',
        'dziesiaty': '10',
        'dziesiatego': '10',
        'jedenascie': '11',
        'jedenasta': '11',
        'jedenastej': '11',
        'jedenasty': '11',
        'jedenastego': '11',
        'dwanascie': '12',
        'dwunasta': '12',
        'dwunastej': '12',
        'dwunasty': '12',
        'dwunastego': '12',
        'trzynascie': '13',
        'trzynasta': '13',
        'trzynastej': '13',
        'trzynasty': '13',
        'trzynastego': '13',
        'czternascie': '14',
        'czternasta': '14',
        'czternastej': '14',
        'czternasty': '14',
        'czternastego': '14',
        'pietnascie': '15',
        'pietnasta': '15',
        'pietnastej': '15',
        'pietnasty': '15',
        'pietnastego': '15',
        'szesnascie': '16',
        'szesnasta': '16',
        'szesnastej': '16',
        'szesnasty': '16',
        'szesnastego': '16',
        'siedemnascie': '17',
        'siedemnasta': '17',
        'siedemnastej': '17',
        'siedemnasty': '17',
        'siedemnastego': '17',
        'osiemnascie': '18',
        'osiemnasta': '18',
        'osiemnastej': '18',
        'osiemnasty': '18',
        'osiemnastego': '18',
        'dziewietnaście': '19',
        'dziewietnasta': '19',
        'dziewietnastej': '19',
        'dziewietnasty': '19',
        'dziewietnastego': '19',
        'dwadziescia': '20',
        'dwudziesta': '20',
        'dwudziestej': '20',
        'dwudziesty': '20',
        'dwudziestego': '20',
        'trzydziesci': '30',
        'trzydziesty': '30',
        'trzydziestego': '30',
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

    TIME_RELATION_WORDS = {
        'za': 'in',
        'o': 'at',
        'na': 'at',
        'po': 'after',
        'nastepny': 'next',
        'nastepnego': 'next',
        'nastepnym': 'next',
        'kolejny': 'next',
        'kolejnego': 'next',
        'kolejnym': 'next',
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

    def __init__(self, clock: Clock):
        self._now = clock.now()

    def __call__(self, text: str) -> EventParsingResult:
        normalized_text = PolishParser._normalize(text)
        tokens = PolishParser._tokenize(normalized_text)
        reduced_tokens = PolishParser._reduce(tokens)
        tagged_tokens = [token for token in reduced_tokens if token.tags]
        time, remaining_tokens = self.seek_time_unequivocal(tagged_tokens)
        date_, remaining_tokens = self.seek_date_unequivocal(remaining_tokens)
        datetime_ = datetime(year=date_.year, month=date_.month, day=date_.day) + time
        untagged_tokens = [token for token in reduced_tokens if not token.tags]
        event_name = self.seek_name(untagged_tokens, text)
        return EventParsingResult(event_name, datetime_)

    def seek_time_unequivocal(self, tokens: List[Token]) -> (Optional[timedelta], List[Token]):
        return self.parse(tokens, UNEQUIVOCAL_TIME_PATTERNS)

    def seek_date_unequivocal(self, tokens: List[Token]) -> (Optional[date], List[Token]):
        return self.parse(tokens, UNEQUIVOCAL_DATE_PATTERNS)

    def seek_name(self, untagged_tokens: List[Token], original_text: str) -> str:
        return original_text

    def parse(self, tokens: List[Token], patterns: Dict[str, List[Tag]]) \
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
        words = [PolishParser.NUMBERS_AS_WORDS[word] if word in PolishParser.NUMBERS_AS_WORDS
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
        reducer_types = (SeparatorNoTagReducer, NoTagReducer, DayPortionReducer)
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
        return token

    @staticmethod
    def _normalize_polish_diacritics(word: str) -> str:
        for diacritic, normalized in PolishParser.POLISH_DIACRITICS.items():
            word = word.replace(diacritic, normalized)
        return word
