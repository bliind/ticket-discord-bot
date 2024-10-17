import discord

class ButtonView(discord.ui.View):
    def __init__(self, timeout, callback):
        super().__init__(timeout=timeout)
        self.callback = callback

    @discord.ui.button(label='Create Channel', style=discord.ButtonStyle.primary, custom_id='ticket_bot_create_channel')
    async def button_remove_sr(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.callback(interaction)
