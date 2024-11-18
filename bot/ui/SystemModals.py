from __init__ import bot, db
import discord

class SetupView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.page = 0
        self.lenght = 5
        self.canceled = True
        self.initialised = False
        self.value = None
        
        self.to_configure = {
            'autorole_id': 'role',
            'announce_channel_id': 'channel',
            'updates_channel_id': 'channel',
            'roles_select_channel': 'channel',
            'groups_channel_category_id': 'category',
        }
        
        for item in self.to_configure.keys():
            setattr(self, item, None)

        # Set roles for select options
        roles = ctx.guild.roles
        self.select_roles = []
        
        if roles is None:
            self.select_roles = discord.SelectOption(label="No Roles Found", value="none")
        else:
            if len(roles) > 25:
                roles = roles[:25]
                
            for role in roles:
                self.select_roles.append(discord.SelectOption(label=role.name, value=str(role.id)))
                
        channels = ctx.guild.text_channels
        self.select_channels = []
        
        if channels is None:
            self.select_channels = discord.SelectOption(label="No Channels Found", value="none")
        else:
            if len(channels) > 24:
                channels = channels[:24]
                
            for channel in channels:
                self.select_channels.append(discord.SelectOption(label=channel.name, value=str(channel.id)))
            
        categories = ctx.guild.categories
        self.select_categories = []
        
        if categories is None:
            self.select_categories = discord.SelectOption(label="No Categories Found", value="none")
        else:
            if len(categories) > 24:
                categories = categories[:24]
                
            for category in categories:
                self.select_categories.append(discord.SelectOption(label=category.name, value=str(category.id)))
            
    async def update_page(self):
        if self.page < 0:
            self.page = 0
        if self.page == 0:
            self.previous_button.disabled = True
        else:
            self.previous_button.disabled = False
        if self.page >= self.lenght:
            self.canceled = False
            self.stop()
            return
        if self.initialised is False:
            self.initialised = True
            self.page = 0
            self.next_button.label = "Next"
        
        current_item = list(self.to_configure.keys())[self.page]
        
        if self.value == 'none':
            self.value = None
        
        if self.value is not None:
            setattr(self, current_item, self.value)
            self.value = None
        
        item = getattr(self, str(current_item))
        
        embed = discord.Embed(
            title="Setup",
        )
        embed.add_field(name="Current Item", value=current_item.replace('_', ' '))
        
        self.select_item.placeholder = f"Select a {current_item.replace('_', ' ')}..."
        if self.to_configure[current_item] == 'role':
            self.select_item.options = self.select_roles
            if item is not None:
                item = discord.utils.get(self.ctx.guild.roles, id=int(item))
                embed.add_field(name="Current Value", value=item.mention if item is not None else "None")
        elif self.to_configure[current_item] == 'channel':
            self.select_item.options = self.select_channels
            if item is not None:
                item = discord.utils.get(self.ctx.guild.text_channels, id=int(item))
                embed.add_field(name="Current Value", value=item.mention if item is not None else "None")
        elif self.to_configure[current_item] == 'category':
            self.select_item.options = self.select_categories
            if item is not None:
                item = discord.utils.get(self.ctx.guild.categories, id=int(item))
                embed.add_field(name="Current Value", value=item.mention if item is not None else "None")

        return self, embed
        
    @discord.ui.select(placeholder="--- Select one ---", options=[discord.SelectOption(label="Start", value="none")])
    async def select_item(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.value = select.values[0]
        
        await interaction.response.defer()
        newView = await self.update_page()
        try:
            await interaction.edit_original_response(view=newView[0], embed=newView[1])
        except TypeError:
            pass
                
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page > 0:
            self.page -= 1
        await interaction.response.defer()
        newView = await self.update_page()
        try:
            await interaction.edit_original_response(view=newView[0], embed=newView[1])
        except TypeError:
            pass

        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.canceled = True
        self.stop()
    
    @discord.ui.button(label="Start", style=discord.ButtonStyle.secondary)
    async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page += 1
        await interaction.response.defer()
        newView = await self.update_page()
        await interaction.edit_original_response(view=newView[0], embed=newView[1])
        
    
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
        