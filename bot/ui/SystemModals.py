from __init__ import bot, db
import discord

class SetupView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        
        self.default_role = None
        self.user_update_channel = None
        self.admin_updates_channel = None

        # Set roles for select options
        roles = ctx.guild.roles
        select_roles = []
        
        if roles is None:
            select_roles = discord.SelectOption(label="No Roles Found", value="none")
        else:
            if len(roles) > 25:
                roles = roles[:25]
                
            for role in roles:
                select_roles.append(discord.SelectOption(label=role.name, value=str(role.id)))
        
        self.default_role_callback.options = select_roles
        
        channels = ctx.guild.text_channels
        select_channels = []
        
        if channels is None:
            select_channels = discord.SelectOption(label="No Channels Found", value="none")
        else:
            if len(channels) > 25:
                channels = channels[:25]
                
            for channel in channels:
                select_channels.append(discord.SelectOption(label=channel.name, value=str(channel.id)))
                
        self.default_channel_callback.options = select_channels
        self.updates_channel_callback.options = select_channels


    # TODO: Implement the setup menu
    @discord.ui.select(placeholder="Default Role", options=[discord.SelectOption(label="No Roles Found", value="none")])
    async def default_role_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.default_role = select.values[0]
        await interaction.response.defer()
        
    @discord.ui.select(placeholder="Announcement Channel", options=[discord.SelectOption(label="No Channels Found", value="none")])
    async def default_channel_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.user_updates_channel = select.values[0]
        await interaction.response.defer()
        
    @discord.ui.select(placeholder="Admin Updates Channel", options=[discord.SelectOption(label="No Channels Found", value="none")])
    async def updates_channel_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.admin_updates_channel = select.values[0]
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.user_updates_channel = None
        self.default_role = None
        self.admin_updates_channel = None
        await interaction.response.send_message("Setup cancelled.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Setup", style=discord.ButtonStyle.primary)
    async def setup(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.default_role is None or self.user_updates_channel is None or self.admin_updates_channel is None:
            await interaction.response.send_message("Please select a default role and announcement channel.", ephemeral=True)
            return
        
        await interaction.response.defer()
        self.stop()
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Bad hooman, this isn't for you.", ephemeral=True)
            return False
        return await super().interaction_check(interaction)

class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.choice = False
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def no_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.choice = False
        await interaction.response.defer()
        self.stop()
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def yes_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.choice = True
        await interaction.response.defer()
        self.stop()
        
class EnterStringModal(discord.ui.Modal):
    def __init__(self, title, fieldName):
        super().__init__(title=title)
        self.title = title
        self.fieldName = fieldName
        self.result = None
        
        self.add_item(discord.ui.InputText(label=fieldName, placeholder="Enter a value..."))
        
    async def callback(self, interaction: discord.Interaction):
        self.result = self.children[0].value
        await interaction.response.send_message(content=f"Entered {self.fieldName}: {self.result}", ephemeral=True)
        self.stop()
        