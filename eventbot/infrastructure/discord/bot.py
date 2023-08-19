from eventbot.domain import CalendarUnitOfWork
from eventbot.domain import Clock

import nextcord
from nextcord.ext import commands

from eventbot.infrastructure.discord.modal import EventModal
from eventbot.infrastructure.discord.notifier import DiscordTextChannelNotifier
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

    @bot.slash_command('event')
    async def add_event(interaction: nextcord.Interaction):
        notifier = DiscordTextChannelNotifier(interaction)
        modal = EventModal(uow, notifier, clock, config.language)
        await interaction.response.send_modal(modal)

    bot.run(token)
