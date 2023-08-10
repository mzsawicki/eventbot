import nextcord
from nextcord.ext import commands

intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents)


@bot.event
async def on_ready():
    print('Ready')


@bot.slash_command('event')
async def main(interaction: nextcord.Interaction):
    pass


@main.subcommand('add')
async def add(interaction: nextcord.Interaction):
    await interaction.send('Test')


def run_bot(token: str):
    bot.run(token)
