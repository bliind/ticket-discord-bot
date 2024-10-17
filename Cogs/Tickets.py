import discord
import json
from discord import app_commands
from discord.ext import commands
from TicketModal import TicketModal
from ButtonView import ButtonView

def load_config():
    global config
    with open('config.json', encoding='utf8') as stream:
        config = json.load(stream)
load_config()

def char_range(c1, c2):
    return [chr(c) for c in range(ord(c1), ord(c2)+1)]

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # add commands to the tree on load
    async def cog_load(self):
        self.bot.command_list.append(self.make_channel_button)

    # remove commands from the tree on load
    async def cog_unload(self):
        for server in self.bot.guilds:
            self.bot.tree.remove_command('make_channel_button', guild=server)

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            view = ButtonView(timeout=None, callback=self.show_ticket_modal)
            self.bot.add_view(view)
        except Exception as e:
            print('Initializing view failed:', e)

    async def create_ticket_channel(self, server, category_id, creator, channel_name):
        overwrites = {
            server.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        user = await self.bot.fetch_user(creator.id)
        overwrites[user] = discord.PermissionOverwrite(read_messages=True)

        try: category = [c for c in server.categories if c.id == category_id][0]
        except: return 'Could not find category'

        try: channel = await category.create_text_channel(channel_name, overwrites=overwrites)
        except Exception as e:
            print(f'Could not create channel: {e}')
            return 'Could not create channel'

        return channel.id

    # says hellos
    @app_commands.command(name='make_channel_button', description='Make channel button dialog')
    async def make_channel_button(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.delete_original_response()
        view = ButtonView(timeout=None, callback=self.show_ticket_modal)
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title='Registration',
            description='Click the button below and enter your SNAP ID to unlock your personal channel and complete your registration on the server. This step is essential as it will grant you access to all other channels.'
        )
        await interaction.channel.send(embed=embed, view=view)
        await view.wait()

    # callback for the button press
    async def show_ticket_modal(self, interaction):
        # shortcut to server-specific configs
        cfg = config[str(interaction.guild.id)]

        # don't work for already registered people
        role_ids = [role.id for role in interaction.user.roles]
        if cfg['registered_role'] in role_ids:
            await interaction.response.send_message('You have already registered!', ephemeral=True)
            return

        # get the input from the user
        modal = TicketModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        channel_name = modal.channel_name.value

        # no value, no op
        if not channel_name:
            return

        # get the categories from the config
        try:
            categories = cfg['categories']
        except KeyError:
            print(f'Could not find guild with ID {interaction.guild.id}')
            return

        # find the category
        for category in categories.keys():
            c1, c2 = category.split('-')
            if channel_name[0] in char_range(c1, c2):
                break

        channel_name = channel_name.replace('#', '-')

        # create new channel with name in categories[category]
        channel_id = await self.create_ticket_channel(interaction.guild, categories[category], interaction.user, channel_name)
        if isinstance(channel_id, int):
            embed = discord.Embed(color=discord.Color.blue(), description=f'<#{channel_id}> created')
            # add registered role to the user
            await interaction.user.add_roles(discord.Object(id=cfg['registered_role']))
        else:
            embed = discord.Embed(color=discord.Color.red(), description=f'Error: {channel_id}')

        await interaction.followup.send(embed=embed, ephemeral=True)
