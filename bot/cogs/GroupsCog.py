from tokenize import group
import discord
from discord.ext import commands
from sqlalchemy import desc
from ui.SessionModals import SessionSelectView
from ui.groupModals import GroupBrowseView, GroupSelectView, GroupEditView
from models import Session, Group, GroupJoin
from __init__ import db


class groupsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    groups_command_group = discord.SlashCommandGroup(name="group", help="Group management commands.", guild_ids=[977513866097479760])
    
    @groups_command_group.command(name="create", description="Create a new group.")
    async def group_create(self, ctx, name):
        selectSessionEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to create a group for.",
            color=discord.Color.blue()
        )
        selectSessionView = SessionSelectView(ctx)
        msg = await ctx.respond(embed=selectSessionEmbed, view=selectSessionView, ephemeral=True)
        await selectSessionView.wait()
        
        if selectSessionView.session is None:
            await msg.edit(content="No session selected.", view=None, embed=None)
            return
        
        session = selectSessionView.session
        session = db.query(Session).filter(Session.id == session).first()
        if session is None:
            await msg.edit(content="Invalid session selected.", view=None, embed=None)
            return
        group = Group(name=name, owner_id=ctx.author.id, session_id=session.id)
        db.add(group)
        db.commit()
        
        successEmbed = discord.Embed(
            title="Group created",
            description=f"Group `{name}` has been created for session {session.name}.",
            color=discord.Color.green()
        )
        await msg.edit(embed=successEmbed, view=None)
        
    @groups_command_group.command(name="delete", description="Delete a group.")
    async def group_delete(self, ctx):
        groups = db.query(Group).filter(Group.owner_id == ctx.author.id).all()
        if len(groups) == 0:
            await ctx.respond("You do not own any groups.", ephemeral=True)
            return
        
        groupSelectEmbed = discord.Embed(
            title="Select a group to delete",
            description="Select a group to delete.",
            color=discord.Color.blue()
        )
        groupSelectView = GroupSelectView(groups)
        msg = await ctx.respond(embed=groupSelectEmbed, view=groupSelectView, ephemeral=True)
        await groupSelectView.wait()
        
        if groupSelectView.selected_group is None:
            await msg.edit(content="No group selected.", view=None, embed=None)
            return
        
        group = groupSelectView.selected_group
        group = db.query(Group).filter(Group.id == group).first()
        if group is None:
            await msg.edit(content="Invalid group selected.", view=None, embed=None)
            return
        db.delete(group)
        db.commit()
        
        successEmbed = discord.Embed(
            title="Group deleted",
            description=f"Group `{group.name}` has been deleted.",
            color=discord.Color.green()
        )
        
        await msg.edit(embed=successEmbed, view=None)
        
    @groups_command_group.command(name="browse", description="Browse groups.")
    async def group_browse(self, ctx):
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to browse groups for.",
            color=discord.Color.blue()
        )
        sessionSelectView = SessionSelectView(ctx)
        msg = await ctx.respond(embed=sessionSelectEmbed, view=sessionSelectView, ephemeral=True)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await msg.edit(content="No session selected.", view=None, embed=None)
            return
        
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        if session is None:
            await msg.edit(content="Invalid session selected.", view=None, embed=None)
            return
        
        groups = db.query(Group).filter(Group.session_id == session.id).all()
        if len(groups) == 0:
            await msg.edit(content="No groups found.", view=None, embed=None)
            return
        
        groupBrowseEmbed = discord.Embed(
            title="Group browser",
            description="Select a group to join.",
            color=discord.Color.blue()
        )
        groupBrowseView = GroupBrowseView(ctx=ctx, groups=groups)
        await groupBrowseView.update()
        msg = await msg.edit(embed=groupBrowseEmbed, view=groupBrowseView)
        await groupBrowseView.wait()
        
        if groupBrowseView.selected_group is None:
            await msg.edit(content="No group selected.", view=None, embed=None)
            return
        
        group = db.query(Group).filter(Group.id == groupBrowseView.selected_group).first()
        if group is None:
            await msg.edit(content="Invalid group selected.", view=None, embed=None)
            return
        
        groupJoin = GroupJoin(user_id=ctx.author.id, group_id=group.id)
        db.add(groupJoin)
        db.commit()
        
        successEmbed = discord.Embed(
            title="Group joined",
            description=f"You have joined group `{group.name}`.",
            color=discord.Color.green()
        )
        await msg.edit(embed=successEmbed, view=None)
    
    @groups_command_group.command(name="leave", description="Leave a group.")
    async def group_leave(self, ctx):
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to leave a group from.",
            color=discord.Color.blue()
        )
        sessionSelectView = SessionSelectView(ctx)
        msg = await ctx.respond(embed=sessionSelectEmbed, view=sessionSelectView, ephemeral=True)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await msg.edit(content="No session selected.", view=None, embed=None)
            return
        
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        if session is None:
            await msg.edit(content="Invalid session selected.", view=None, embed=None)
            return
        
        groups_all = db.query(Group).filter(Group.session_id == session.id).all()
        groups = []
        
        for group in groups_all:
            if db.query(GroupJoin).filter_by(user_id=ctx.author.id, group_id=group.id).first():
                groups.append(group)
        if len(groups) == 0:
            await msg.edit(content="No groups found.", view=None, embed=None)
            return
        
        groupSelectEmbed = discord.Embed(
            title="Select a group to leave",
            description="Select a group to leave.",
            color=discord.Color.blue()
        )
        groupSelectView = GroupSelectView(groups)
        msg = await ctx.respond(embed=groupSelectEmbed, view=groupSelectView, ephemeral=True)
        await groupSelectView.wait()
        if groupSelectView.selected_group is None:
            await msg.edit(content="No group selected.", view=None, embed=None)
            return
        
        group = db.query(Group).filter(Group.id == groupSelectView.selected_group).first()
        if group is None:
            await msg.edit(content="Invalid group selected.", view=None, embed=None)
            return
        
        groupJoin = db.query(GroupJoin).filter(GroupJoin.user_id == ctx.author.id, GroupJoin.group_id == group.id).first()
        if groupJoin is None:
            await msg.edit(content="You are not in this group.", view=None, embed=None)
            return
        
        db.delete(groupJoin)
        db.commit()
        
        successEmbed = discord.Embed(
            title="Group left",
            description=f"You have left group `{group.name}`.",
            color=discord.Color.green()
        )
        await msg.edit(embed=successEmbed, view=None)
        
    @groups_command_group.command(name="edit", description="Edit a group.")
    async def group_edit(self, ctx):
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to edit a group for.",
            color=discord.Color.blue()
        )
        sessionSelectView = SessionSelectView(ctx)
        msg = await ctx.respond(embed=sessionSelectEmbed, view=sessionSelectView, ephemeral=True)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await msg.edit(content="No session selected.", view=None, embed=None)
            return
        
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        if session is None:
            await msg.edit(content="Invalid session selected.", view=None, embed=None)
            return
    
        groups = db.query(Group).filter(Group.owner_id == ctx.author.id, Group.session_id == session.id).all()
        if len(groups) == 0:
            await msg.edit(content="No groups found.", view=None, embed=None)
            return
        
        groupSelectEmbed = discord.Embed(
            title="Select a group to edit",
            description="Select a group to edit.",
            color=discord.Color.blue()
        )
        groupSelectView = GroupSelectView(groups)
        await msg.edit(embed=groupSelectEmbed, view=groupSelectView, )
        await groupSelectView.wait()
        if groupSelectView.selected_group is None:
            await msg.edit(content="No group selected.", view=None, embed=None)
            return
        
        group = db.query(Group).filter(Group.id == groupSelectView.selected_group).first()
        if group is None:
            await msg.edit(content="Invalid group selected.", view=None, embed=None)
            return
        
        groupEditEmbed = discord.Embed(
            title="Edit group",
            description=f"""Use the buttons below to update the group. 
            Current group details are shown below. \n
            Name: {group.name}
            Description: {group.description}
            """,
            color=discord.Color.blue()
        )
        groupEditView = GroupEditView(group=group)
        await msg.edit(embed=groupEditEmbed, view=groupEditView)
        await groupEditView.wait()
        change = False
        if groupEditView.name_is_edited or groupEditView.description_is_edited:
            if groupEditView.name_is_edited and groupEditView.name is not None:
                group.name = groupEditView.name
            if groupEditView.description_is_edited and groupEditView.description is not None:
                group.description = groupEditView.description
            db.add(group)
            db.commit()
            change = True
        
        if change:
            await msg.edit(content="Group changes have been registered and should update soon!", view=None, embed=None)
        else:
            await msg.edit(content="No changes were made, nothing happened!", view=None, embed=None)
            
def setup(bot):
    bot.add_cog(groupsCog(bot))