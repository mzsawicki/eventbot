import asyncio
from datetime import datetime
from typing import List, Optional

import nextcord

from eventbot.domain import Notifier
from eventbot.infrastructure.config import Config
from eventbot.infrastructure.discord.menu import EventMenu
from eventbot.infrastructure.discord.strings import StringType, STRINGS


def format_time(time: datetime) -> str:
    return f'{time.day}.{time.month:02d}.{time.year}, {time.hour:02d}:{time.minute:02d}'


class DiscordTextChannelNotifier(Notifier):
    def __init__(self, interaction: nextcord.Interaction):
        config = Config()
        self._language = config.language
        self._interaction = interaction

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
        message = message_template.format(owner=owner, event_name=event_name,
                                          event_code=event_code, time=format_time(time))
        loop = asyncio.get_running_loop()
        loop.create_task(EventMenu(message).prompt(self._interaction))

