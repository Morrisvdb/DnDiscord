from math import e
import discord
from __init__ import bot, db
from models import GroupJoin, Group
from ui.SystemModals import EnterStringModal


class GroupBrowseView(discord.ui.View):
    def __init__(self, ctx, groups):
        super().__init__()
        self.ctx = ctx
        self.groups = groups
        self.page = 0
        self.selected_group = None
        self.sub = None
                
    async def update(self):
        if self.sub:
            self.select_group.disabled = True
            self.next.disabled = True
            self.previous.disabled = True
            self.details.label = "Back"
            
            group = db.query(Group).filter_by(id=self.sub).first()
            if group is None:
                return 0
            owner_name = await bot.fetch_user(group.owner_id)
            if self.ctx.author.id == group.owner_id:
                owner_name = "You"
            else:
                if owner_name is None:
                    owner_name = "Unknown"
                else:
                    owner_name = owner_name.name
            embed = discord.Embed(
                title=group.name + " - " + owner_name,
                description=group.description,
                color=discord.Color.blue()
            )
            return embed
            
        self.select_group.disabled = False
        self.next.disabled = False
        self.previous.disabled = False
        self.details.label = "Details"
        selectable_groups = []       
        for group in self.groups[self.page * 5:self.page * 5 + 5]:
            owner_name = await bot.fetch_user(group.owner_id)
            if int(self.ctx.author.id) == int(group.owner_id):
                owner_name = "You"
            else:
                if owner_name is None:
                    owner_name = "Unknown"
                else:
                    owner_name = owner_name.name
            joins = db.query(GroupJoin).filter_by(user_id=self.ctx.author.id, group_id=group.id).all()
            joined = True if joins else False
            label = group.name
            if joined:
                label = group.name + " - (Joined)"
            elif int(self.ctx.author.id) == int(group.owner_id):    
                label = group.name + " - (Owner)"
            
            selectable_groups.append(discord.SelectOption(label=label, description=f"Owner: {owner_name}", value=str(group.id)))
        self.select_group.options = selectable_groups
        embed = discord.Embed(
            title="Groups",
            description="Select a group to join.",
            color=discord.Color.blue()
        )
        return embed
        
    @discord.ui.select(placeholder="Select a group", options=[discord.SelectOption(label="Loading...", description="Please wait...")])
    async def select_group(self, select, interaction):
        self.selected_group = select.values[0]
        await interaction.response.defer()
        
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, button, interaction):
        if self.page == 0:
            return
        self.page -= 1
        await self.update()
        await interaction.response.edit_message(view=self)
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        self.selected_group = None
        await interaction.response.defer()
        self.stop()
        
    @discord.ui.button(label="Details", style=discord.ButtonStyle.grey)
    async def details(self, button, interaction):
        if self.sub is None:
            self.sub = self.selected_group
            embed = await self.update()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            self.sub = None
            embed = await self.update()
            await interaction.response.edit_message(embed=embed, view=self)
        
    @discord.ui.button(label="Join", style=discord.ButtonStyle.green)
    async def select(self, button, interaction):
        if self.selected_group is None:
            await interaction.response.send_message("Please select a group first.", ephemeral=True)
            return
        group_join = db.query(GroupJoin).filter_by(user_id=self.ctx.author.id, group_id=str(self.selected_group)).first()
        if group_join:
            await interaction.response.send_message("You have already joined this group.", ephemeral=True)
            return
        self.stop()
        
    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next(self, button, interaction):
        if self.page == len(self.groups) // 5:
            return
        self.page += 1
        await self.update()
        await interaction.response.edit_message(view=self)

class GroupSelectView(discord.ui.View):
    def __init__(self, groups):
        """Creates a menu with a select to choose a group

        Args:
            groups (list): A list of all the groups (SQA objects) to be displayed in the select
        """
        super().__init__()
        self.groups = groups
        self.selected_group = None
        
        selectable_groups = []
        for group in groups:
            owner_name = bot.get_user(group.owner_id)
            if owner_name is None:
                owner_name = "Unknown"
            else:
                owner_name = owner_name.name
            selectable_groups.append(discord.SelectOption(label=group.name, description=f"Owner: {owner_name}", value=str(group.id)))
        self.select_group.options = selectable_groups
        
    @discord.ui.select(placeholder="Select a group", options=[discord.SelectOption(label="Loading...", description="Please wait...")])
    async def select_group(self, select, interaction):
        self.selected_group = select.values[0]
        await interaction.response.defer()
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        self.selected_group = None
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Select", style=discord.ButtonStyle.green)
    async def select(self, button, interaction):
        if self.selected_group is None:
            await interaction.response.send_message("Please select a group first.", ephemeral=True)
            return
        self.stop()
        
class GroupEditView(discord.ui.View):
    def __init__(self, group):
        super().__init__()
        self.group = group
        self.name = group.name
        self.description = group.description
        self.private = group.private
        
        self.name_is_edited = False
        self.description_is_edited = False
        self.private_is_edited = False
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        self.name_is_edited = False
        self.description_is_edited = False
        self.private_is_edited = False
        self.stop()
        
    @discord.ui.button(label="Edit Name", style=discord.ButtonStyle.grey)
    async def edit_name(self, button, interaction):
        enterStringModal = EnterStringModal("Enter a new name for the group.", fieldName="Name")
        await interaction.response.send_modal(enterStringModal)
        await enterStringModal.wait()
        if enterStringModal.result is None:
            return
        
        self.name = enterStringModal.result
        self.name_is_edited = True
        
    @discord.ui.button(label="Edit Description", style=discord.ButtonStyle.grey)
    async def edit_description(self, button, interaction):
        enterStringModal = EnterStringModal("Enter a new description for the group.", fieldName="Description")
        await interaction.response.send_modal(enterStringModal)
        await enterStringModal.wait()
        if enterStringModal.result is None:
            return
        
        self.description = enterStringModal.result
        self.description_is_edited = True
        
    @discord.ui.button(label="Make Public", style=discord.ButtonStyle.grey)
    async def make_public(self, button, interaction):
        self.private = False
        self.private_is_edited = True
        await interaction.response.defer()
        
    @discord.ui.button(label="Make Private", style=discord.ButtonStyle.grey)
    async def make_private(self, button, interaction):
        self.private = True
        self.private_is_edited = True
        await interaction.response.defer()
        
    @discord.ui.button(label="Save", style=discord.ButtonStyle.green)
    async def save(self, button, interaction):
        self.stop()
        
class ViewInvitesView(discord.ui.View):
    def __init__(self, invites):
        super().__init__()
        self.invites = invites
        self.page = 0
        self.action = None
    
    async def update(self):
        selectable_invites = []
        for invite in self.invites[self.page * 5:self.page * 5 + 5]:
            group = db.query(Group).filter_by(id=invite.group_id).first()
            group_owner_name = await bot.fetch_user(group.owner_id)
            if group_owner_name is None:
                group_owner_name = "Unknown"
            else:
                group_owner_name = group_owner_name.name
            selectable_invites.append(discord.SelectOption(label=group_owner_name, value=str(invite.id)))
        self.select_invite.options = selectable_invites
        embed = discord.Embed(
            title="Invites",
            description="Select an invite to delete.",
            color=discord.Color.blue()
        )
        return embed
    
    @discord.ui.select(placeholder="Select an invite", options=[discord.SelectOption(label="Loading...", description="Please wait...")])
    async def select_invite(self, select, interaction):
        self.selected_invite = select.values[0]
        await interaction.response.defer()
        
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, button, interaction):
        if self.page == 0:
            return
        self.page -= 1
        await self.update()
        await interaction.response.edit_message(view=self)
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        self.selected_invite = None
        await interaction.response.defer()
        self.stop()
        
    @discord.ui.button(label="Join", style=discord.ButtonStyle.green)
    async def join(self, button, interaction):
        if self.selected_invite is None:
            await interaction.response.send_message("Please select an invite first.", ephemeral=True)
            return
        self.action = 'accept'
        self.stop()
        
    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
    async def delete(self, button, interaction):
        if self.selected_invite is None:
            await interaction.response.send_message("Please select an invite first.", ephemeral=True)
            return
        self.action = 'delete'
        self.stop()
        
    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next(self, button, interaction):
        if self.page == len(self.invites) // 5:
            return
        self.page += 1
        await self.update()
        await interaction.response.edit_message(view=self)
           
class GroupsViewView(discord.ui.View):
    def __init__(self, ctx, groups):
        super().__init__()
        self.ctx = ctx
        self.groups = groups
        self.page = 0
        self.selected_group = None
        self.sub = None
                
    async def update(self):
        if self.sub:
            self.select_group.disabled = True
            self.next.disabled = True
            self.previous.disabled = True
            self.details.label = "Back"
            
            group = db.query(Group).filter_by(id=self.sub).first()
            if group is None:
                return 0
            owner_name = await bot.fetch_user(group.owner_id)
            if self.ctx.author.id == group.owner_id:
                owner_name = "You"
            else:
                if owner_name is None:
                    owner_name = "Unknown"
                else:
                    owner_name = owner_name.name
            embed = discord.Embed(
                title=group.name + " - " + owner_name,
                description=group.description,
                color=discord.Color.blue()
            )
            return embed
            
        self.select_group.disabled = False
        self.next.disabled = False
        self.previous.disabled = False
        self.details.label = "Details"
        selectable_groups = []       
        for group in self.groups[self.page * 5:self.page * 5 + 5]:
            owner_name = await bot.fetch_user(group.owner_id)
            if self.ctx.author.id == group.owner_id:
                owner_name = "You"
            else:
                if owner_name is None:
                    owner_name = "Unknown"
                else:
                    owner_name = owner_name.name
            label = group.name
            if int(group.owner_id) == self.ctx.author.id:
                label = group.name + " - (Owner)"
            selectable_groups.append(discord.SelectOption(label=label, description=f"Owner: {owner_name}", value=str(group.id)))
        self.select_group.options = selectable_groups
        embed = discord.Embed(
            title="Groups",
            description="Select a group to view.",
            color=discord.Color.blue()
        )
        return embed
        
    @discord.ui.select(placeholder="Select a group", options=[discord.SelectOption(label="Loading...", description="Please wait...")])
    async def select_group(self, select, interaction):
        self.selected_group = select.values[0]
        await interaction.response.defer()
        
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, button, interaction):
        if self.page == 0:
            return
        self.page -= 1
        await self.update()
        await interaction.response.edit_message(view=self)
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        self.selected_group = None
        await interaction.response.defer()
        self.stop()
        
    @discord.ui.button(label="Details", style=discord.ButtonStyle.grey)
    async def details(self, button, interaction):
        if self.sub is None:
            self.sub = self.selected_group
            embed = await self.update()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            self.sub = None
            embed = await self.update()
            await interaction.response.edit_message(embed=embed, view=self)
        
    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next(self, button, interaction):
        if self.page == len(self.groups) // 5:
            return
        self.page += 1
        await self.update()
        await interaction.response.edit_message(view=self)
