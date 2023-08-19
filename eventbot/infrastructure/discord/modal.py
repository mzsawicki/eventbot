import nextcord

from eventbot.domain import CalendarUnitOfWork, Notifier, Clock, Calendar, CalendarLanguage
from eventbot.infrastructure.discord.strings import STRINGS, StringType


class EventModal(nextcord.ui.Modal):
    def __init__(self, uow: CalendarUnitOfWork, notifier: Notifier, clock: Clock, language: CalendarLanguage):
        super().__init__(
            STRINGS[language][StringType.MODAL_TITLE],
            timeout=5 * 60,
        )
        self._uow = uow
        self._notifier = notifier
        self._clock = clock
        self._language = language

        self.name = nextcord.ui.TextInput(
            label=STRINGS[language][StringType.MODAL_EVENT_NAME_LABEL],
            min_length=3,
            max_length=64,
        )
        self.add_item(self.name)

        self.time_prompt = nextcord.ui.TextInput(
            label=STRINGS[language][StringType.MODAL_EVENT_TIME_LABEL],
            style=nextcord.TextInputStyle.paragraph,
            placeholder=STRINGS[language][StringType.MODAL_EVENT_TIME_PLACEHOLDER],
            required=True,
            max_length=128,
        )
        self.add_item(self.time_prompt)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        guild = interaction.guild.name
        channel = interaction.channel.name
        user = interaction.user.mention
        prompt = ' '.join([self.name.value, self.time_prompt.value])
        with self._uow as uow:
            if not uow.calendars.does_calendar_exist(guild, channel):
                calendar = Calendar(guild, channel, language=self._language)
            else:
                calendar = self._uow.calendars.get_calendar_by_guild_and_channel(guild, channel)
            calendar.add_event(prompt, user, self._clock, uow.event_sequence_generator, self._notifier)
            uow.calendars.add_calendar(calendar)
            uow.commit()
