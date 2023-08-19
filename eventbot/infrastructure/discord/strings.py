from enum import Enum

from eventbot.domain import CalendarLanguage


class StringType(Enum):
    EVENT_START_MESSAGE = 'start'
    EVENT_REMINDER_MESSAGE = 'reminder'
    EVENT_CREATED_MESSAGE = 'created'
    MODAL_TITLE = 'modal_title'
    MODAL_EVENT_NAME_LABEL = 'modal_event_name_label'
    MODAL_EVENT_TIME_LABEL = 'modal_event_time_label'
    MODAL_EVENT_TIME_PLACEHOLDER = 'modal_event_time_placeholder'


STRINGS = {
    CalendarLanguage.PL: {
        StringType.EVENT_START_MESSAGE: 'Wydarzenie {event_name} ({event_code}) właśnie startuje!\n{handles}',
        StringType.EVENT_REMINDER_MESSAGE: 'Wydarzenie {event_name} ({event_code})'
                                           ' wystartuje wkrótce: {time}\n{handles}',
        StringType.EVENT_CREATED_MESSAGE: 'Nowe wydarzenie utworzone przez: {owner}\n\n'
                             '# {event_name}\n'
                             'Kiedy: {time}\n'
                             'Kod wydarzenia: {event_code}',
        StringType.MODAL_TITLE: 'Nowe wydarzenie',
        StringType.MODAL_EVENT_NAME_LABEL: 'Tytuł',
        StringType.MODAL_EVENT_TIME_LABEL: 'Kiedy?',
        StringType.MODAL_EVENT_TIME_PLACEHOLDER: 'np.: Jutro o 20; W następną sobotę o 10 AM;'
                                                 ' 22 lutego o ósmej wieczorem itd.'

    }
}
