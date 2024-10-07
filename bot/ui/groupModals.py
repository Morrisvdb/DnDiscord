import discord
from __init__ import bot


class GroupBrowseView(discord.ui.View):
    def __init__(self, groups, timeout=None):
        super().__init__()
        self.groups = groups
        self.page = 0
        self.items_per_page = 5
        self.selected_group = None


    def update(self):
        embed = discord.Embed(
            title="Group browser",
            description="Select a group to join.",
            color=discord.Color.blue()
        )
        for group in self.groups[self.page * self.items_per_page:self.page * self.items_per_page + self.items_per_page]:
            embed.add_field(
                name=group.name,
                value=f"Owner: <@{group.owner_id}>"
            )
            
        view = self
        view.select_group.options = [
                discord.SelectOption(label=group.name, description=f"Owner: <@{group.owner_id}>", value=str(group.id))
                for group in self.groups[self.page * self.items_per_page:self.page * self.items_per_page + self.items_per_page]
            ]
            
        return embed, view
    
    @discord.ui.select(placeholder="Select a group to join", options=[discord.SelectOption(label="Loading...", description="Please wait...")])
    async def select_group(self, select, interaction):
        self.selected_group = select.values[0]
        await interaction.response.defer()
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous_page(self, button, interaction):
        if self.page == 0:
            return
        self.page -= 1
        await interaction.response.edit_message(embed=self.update()[0], view=self.update()[1])
        
    @discord.ui.button(label="Join", style=discord.ButtonStyle.green)
    async def join_group(self, button, interaction):
        if self.selected_group is None:
            await interaction.response.send_message("Please select a group first.")
            return
        self.stop()
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        self.selected_group = None
        await interaction.response.defer()
        self.stop()    
        
    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_page(self, button, interaction):
        if self.page == len(self.groups) // self.items_per_page:
            return
        self.page += 1
        await interaction.response.edit_message(embed=self.update()[0], view=self.update()[1])
    
    async def interaction_check(self, interaction):
        if interaction.user.id != interaction.message.embeds[0].author.id:
            await interaction.response.send_message("Bad hooman, this is not for you!")
            return False
        return True
    
    
class GroupSelectView(discord.ui.View):
    # TODO: Do this