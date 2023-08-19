from typing import Optional

import nextcord
from nextcord.ext import menus

from eventbot.domain import CalendarUnitOfWork
from eventbot.infrastructure.discord.strings import StringType, STRINGS
from eventbot.infrastructure.config import Config


class EventMenu(menus.ButtonMenu):
    def __init__(self, msg, event_code: str, event_name: str, uow: CalendarUnitOfWork, config: Config = Config()):
        super().__init__(timeout=None, delete_message_after=False, disable_buttons_after=False)
        self.msg = msg
        self._event_code = event_code
        self._event_name = event_name
        self._uow = uow
        self._initial_message: Optional[nextcord.Message] = None
        self._language = config.language

    async def send_initial_message(self, ctx, channel):
        self._initial_message: nextcord.Message = await channel.send(self.msg, view=self)
        return self._initial_message

    @nextcord.ui.button(label=STRINGS[Config().language][StringType.BUTTON_CONFIRM_LABEL],
                        emoji='\N{WHITE HEAVY CHECK MARK}')
    async def do_confirm(self, button, interaction: nextcord.Interaction):
        with self._uow as unit_of_work:
            calendar = unit_of_work.calendars.get_calendar_by_guild_and_channel(
                interaction.guild.name, interaction.channel.name)
            calendar.declare_yes_to_event(interaction.user.mention, self._event_code)
            unit_of_work.calendars.add_calendar(calendar)
            unit_of_work.commit()
        if not (thread := self._initial_message.thread):
            thread = await self._create_event_thread()
        message = STRINGS[self._language][StringType.DECISION_YES_MESSAGE].format(user=interaction.user.mention)
        await thread.send(message)

    @nextcord.ui.button(label=STRINGS[Config().language][StringType.BUTTON_DENY_LABEL], emoji='\N{CROSS MARK}')
    async def do_deny(self, button, interaction: nextcord.Interaction):
        with self._uow as unit_of_work:
            calendar = unit_of_work.calendars.get_calendar_by_guild_and_channel(
                interaction.guild.name, interaction.channel.name)
            calendar.declare_no_to_event(interaction.user.mention, self._event_code)
            unit_of_work.calendars.add_calendar(calendar)
            unit_of_work.commit()
        if not (thread := self._initial_message.thread):
            thread = await self._create_event_thread()
        message = STRINGS[self._language][StringType.DECISION_NO_MESSAGE].format(user=interaction.user.mention)
        await thread.send(message)

    @nextcord.ui.button(label=STRINGS[Config().language][StringType.BUTTON_MAYBE_LABEL], emoji='\u2754')
    async def do_maybe(self, button, interaction: nextcord.Interaction):
        with self._uow as unit_of_work:
            calendar = unit_of_work.calendars.get_calendar_by_guild_and_channel(
                interaction.guild.name, interaction.channel.name)
            calendar.declare_maybe_to_event(interaction.user.mention, self._event_code)
            unit_of_work.calendars.add_calendar(calendar)
            unit_of_work.commit()
        if not (thread := self._initial_message.thread):
            thread = await self._create_event_thread()
        message = STRINGS[self._language][StringType.DECISION_MAYBE_MESSAGE].format(user=interaction.user.mention)
        await thread.send(message)

    async def prompt(self, ctx):
        await self.start(interaction=ctx, wait=False)

    async def _create_event_thread(self) -> nextcord.Thread:
        return await self._initial_message.create_thread(name=f'{self._event_name} ({self._event_code})')
