from nextcord.ext import menus


class EventMenu(menus.Menu):
    def __init__(self, msg):
        super().__init__(timeout=30.0, delete_message_after=False)
        self.msg = msg
        self.result = None

    async def send_initial_message(self, ctx, channel):
        return await channel.send(self.msg)

    @menus.button('\N{WHITE HEAVY CHECK MARK}')
    async def do_confirm(self, payload):
        pass

    @menus.button('\N{CROSS MARK}')
    async def do_deny(self, payload):
        pass

    async def prompt(self, ctx):
        await self.start(interaction=ctx, wait=True)
        return self.result
