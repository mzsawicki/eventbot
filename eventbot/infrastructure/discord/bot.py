from uuid import UUID

import nextcord
from nextcord.ext import commands, tasks

from eventbot.domain import CalendarUnitOfWork, Clock, Notifier
from eventbot.infrastructure.discord.formatters import format_event
from eventbot.infrastructure.discord.modal import EventModal
from eventbot.infrastructure.discord.notifiers import DiscordEventCreationNotifier, DiscordEventLifecycleNotifier
from eventbot.infrastructure.discord.strings import STRINGS, StringType
from eventbot.infrastructure.config import Config


class CalendarBot(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)


class CalendarCog(commands.Cog):
    def __init__(self, bot: CalendarBot, uow: CalendarUnitOfWork, clock: Clock):
        self._bot = bot
        self._uow = uow
        self._clock = clock
        self.handle_pending_notifications.start()

    @tasks.loop(minutes=1)
    async def handle_pending_notifications(self):
        for channel in self._bot.get_all_channels():
            notifier = DiscordEventLifecycleNotifier(channel)
            guild_handle = channel.guild.name
            channel_handle = channel.name
            await self._handle_calendar(guild_handle, channel_handle, notifier)

    async def _handle_calendar(self, guild: str, channel: str, notifier: Notifier) -> None:
        with self._uow as unit_of_work:
            if unit_of_work.calendars.does_calendar_exist(guild, channel):
                calendar = unit_of_work.calendars.get_calendar_by_guild_and_channel(guild, channel)
                calendar.send_pending_notifications(self._clock, notifier)
                unit_of_work.calendars.add_calendar(calendar)
                unit_of_work.commit()


def run_bot(token: str, uow: CalendarUnitOfWork, clock: Clock, config: Config = Config()) -> None:
    bot = CalendarBot()
    cog = CalendarCog(bot, uow, clock)

    @bot.event
    async def on_ready():
        print('Ready')

    @bot.slash_command('event')
    async def events(interaction: nextcord.Interaction):
        pass

    @events.subcommand('new', description=STRINGS[config.language][StringType.COMMAND_ADD_DESCRIPTION])
    async def add_event(interaction: nextcord.Interaction):
        notifier = DiscordEventCreationNotifier(interaction, uow)
        modal = EventModal(uow, notifier, clock, config.language)
        await interaction.response.send_modal(modal)

    @events.subcommand('list', description=STRINGS[config.language][StringType.COMMAND_LIST_DESCRIPTION])
    async def list_events(interaction: nextcord.Interaction,):
        with uow:
            incoming_events = uow.calendars.get_incoming_events(interaction.guild.name, interaction.channel.name)
            message = '\n'.join([format_event(event) for event in incoming_events])
            await interaction.response.send_message(message)

    bot.add_cog(cog)
    bot.run(token)
