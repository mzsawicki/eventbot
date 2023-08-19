from eventbot.domain import CalendarUnitOfWork, Clock

import nextcord
from nextcord.ext import commands

from eventbot.infrastructure.discord.formatters import format_event
from eventbot.infrastructure.discord.modal import EventModal
from eventbot.infrastructure.discord.notifier import DiscordTextChannelNotifier
from eventbot.infrastructure.discord.strings import STRINGS, StringType
from eventbot.infrastructure.config import Config


class CalendarBot(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)


def run_bot(token: str, uow: CalendarUnitOfWork, clock: Clock, config: Config = Config()) -> None:
    bot = CalendarBot()

    @bot.event
    async def on_ready():
        print('Ready')

    @bot.slash_command('events')
    async def events(interaction: nextcord.Interaction):
        pass

    @events.subcommand('add', description=STRINGS[config.language][StringType.COMMAND_ADD_DESCRIPTION])
    async def add_event(interaction: nextcord.Interaction):
        notifier = DiscordTextChannelNotifier(interaction, uow)
        modal = EventModal(uow, notifier, clock, config.language)
        await interaction.response.send_modal(modal)

    @events.subcommand('list', description=STRINGS[config.language][StringType.COMMAND_LIST_DESCRIPTION])
    async def list_events(interaction: nextcord.Interaction,):
        with uow:
            incoming_events = uow.calendars.get_incoming_events(interaction.guild.name, interaction.channel.name)
            message = '\n'.join([format_event(event) for event in incoming_events])
            await interaction.response.send_message(message)

    bot.run(token)
