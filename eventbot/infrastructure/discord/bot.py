import nextcord
from nextcord.ext import commands

bot = commands.Bot()


@bot.event
async def on_ready():
    print('Ready')


@bot.slash_command('add')
async def add_calendar_event(interaction: nextcord.Interaction):
    await interaction.send('Test')


def run(token: str):
    bot.run(token)
