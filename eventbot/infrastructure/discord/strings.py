from enum import Enum

from eventbot.domain import CalendarLanguage


class StringType(Enum):
    EVENT_START_MESSAGE = 'start'
    EVENT_REMINDER_MESSAGE = 'reminder'
    EVENT_CREATED_MESSAGE = 'created'
    EVENT_REMOVED_MESSAGE = 'removed'
    MODAL_TITLE = 'modal_title'
    MODAL_EVENT_NAME_LABEL = 'modal_event_name_label'
    MODAL_EVENT_TIME_LABEL = 'modal_event_time_label'
    MODAL_EVENT_TIME_PLACEHOLDER = 'modal_event_time_placeholder'
    MODAL_EVENT_REMINDER_LABEL = 'modal_event_reminder_label'
    MODAL_EVENT_REMINDER_PLACEHOLDER = 'modal_event_reminder_placeholder'
    COMMAND_ADD_DESCRIPTION = 'command_add_description'
    COMMAND_LIST_DESCRIPTION = 'command_list_description'
    COMMAND_REMOVE_DESCRIPTION = 'command_remove_description'
    BUTTON_CONFIRM_LABEL = 'button_confirm_label'
    BUTTON_DENY_LABEL = 'button_deny_label'
    BUTTON_MAYBE_LABEL = 'button_maybe_label'
    DECISION_YES_MESSAGE = 'decision_yes_message'
    DECISION_NO_MESSAGE = 'decision_no_message'
    DECISION_MAYBE_MESSAGE = 'decision_maybe_message'


STRINGS = {
    CalendarLanguage.PL: {
        StringType.EVENT_START_MESSAGE: 'Wydarzenie {event_name} ({event_code}) właśnie startuje!\n{handles}',
        StringType.EVENT_REMINDER_MESSAGE: 'Wydarzenie {event_name} ({event_code})'
                                           ' wystartuje wkrótce: {time}\n{handles}',
        StringType.EVENT_CREATED_MESSAGE: '# {event_name}\n'
                                          'Kiedy: {time}\n'
                                          'Zainteresowane osoby zostaną powiadomione: {reminder_time}\n'
                                          'Kod wydarzenia: {event_code}\n'
                                          'Dodane przez: {owner}',
        StringType.EVENT_REMOVED_MESSAGE: 'Wydarzenie {event_code} zostało usunięte.',

        StringType.MODAL_TITLE: 'Nowe wydarzenie',
        StringType.MODAL_EVENT_NAME_LABEL: 'Tytuł',
        StringType.MODAL_EVENT_TIME_LABEL: 'Kiedy?',
        StringType.MODAL_EVENT_TIME_PLACEHOLDER: 'np.: Jutro o 20; W następną sobotę o 10 AM;'
                                                 ' 22 lutego o ósmej wieczorem itd.',
        StringType.MODAL_EVENT_REMINDER_LABEL: 'Ustawić przypomnienie? (opcjonalne)',
        StringType.MODAL_EVENT_REMINDER_PLACEHOLDER: 'np. 10 minut wcześniej; dwie godziny przed itd.',
        StringType.COMMAND_ADD_DESCRIPTION: 'Dodaj nowe wydarzenie do tego kanału',
        StringType.COMMAND_LIST_DESCRIPTION: 'Lista nadchodzących wydarzeń na tym kanale',
        StringType.COMMAND_REMOVE_DESCRIPTION: 'Usuń wydarzenie z tego kanału',
        StringType.BUTTON_CONFIRM_LABEL: 'Wezmę udział',
        StringType.BUTTON_DENY_LABEL: 'Nie wezmę udziału',
        StringType.BUTTON_MAYBE_LABEL: 'Być może',
        StringType.DECISION_YES_MESSAGE: '{user} weźmie udział!',
        StringType.DECISION_NO_MESSAGE: '{user} nie wieźmie udziału :(',
        StringType.DECISION_MAYBE_MESSAGE: '{user} jeszcze się zastanawia...',

    }
}
