import discord
from discord import ui

class TicketModal(ui.Modal, title="Create Channel"):
    channel_name = ui.TextInput(label='Enter SNAP ID')
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
