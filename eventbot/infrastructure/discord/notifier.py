import asyncio
from datetime import datetime
from typing import List, Optional

import nextcord

from eventbot.domain import Notifier, CalendarUnitOfWork
from eventbot.infrastructure.config import Config
from eventbot.infrastructure.discord.formatters import format_time
from eventbot.infrastructure.discord.menu import EventMenu
from eventbot.infrastructure.discord.strings import StringType, STRINGS


class DiscordTextChannelNotifier(Notifier):
    def __init__(self, interaction: nextcord.Interaction, uow: CalendarUnitOfWork):
        config = Config()
        self._language = config.language
        self._interaction = interaction
        self._uow = uow

    def notify_event_start(self, event_name: str, event_code: str, user_handles: List[str]) -> None:
        handles = ' '.join(user_handles)
        message_template = STRINGS[self._language][StringType.EVENT_START_MESSAGE]
        message = message_template.format(event_name=event_name, event_code=event_code, handles=handles)
        loop = asyncio.get_running_loop()
        loop.create_task(self._interaction.channel.send(message))

    def notify_reminder(self, event_name: str, event_code: str, start_time: datetime, user_handles: List[str]) -> None:
        handles = ' '.join(user_handles)
        message_template = STRINGS[self._language][StringType.EVENT_REMINDER_MESSAGE]
        message = message_template.format(event_name=event_name, event_code=event_code,
                                          time=format_time(start_time), handles=handles)
        loop = asyncio.get_running_loop()
        loop.create_task(self._interaction.channel.send(message))

    def notify_event_created(self, event_name: str, event_code: str, time: datetime, owner: str,
                             reminder_time: Optional[datetime] = None) -> None:
        message_template = STRINGS[self._language][StringType.EVENT_CREATED_MESSAGE]
        if not reminder_time:
            reminder_time = time
        message = message_template.format(owner=owner, event_name=event_name,
                                          event_code=event_code, time=format_time(time),
                                          reminder_time=format_time(reminder_time))
        loop = asyncio.get_running_loop()
        menu = EventMenu(message, event_code, event_name, self._uow)
        loop.create_task(menu.prompt(self._interaction))

