import discord
from discord.ext import commands
from sqlalchemy import desc
from ui.SessionModals import SessionSelectView
from ui.groupModals import GroupBrowseView
from models import Session, Group, GroupJoin
from __init__ import db


class groupsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    groups_command_group = discord.SlashCommandGroup(name="group", help="Group management commands.", guild_ids=[977513866097479760])
    
    @groups_command_group.command(name="create", help="Create a new group.")
    async def create_group(self, ctx, name: discord.Option(str, "The name of the group.", min_length=3, max_length=32)):
        sessionSelectView = SessionSelectView(ctx)
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Please select a session to add this group to.",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=sessionSelectEmbed, view=sessionSelectView)
        await sessionSelectView.wait()
        session = sessionSelectView.session
        session = db.query(Session).filter_by(id=int(session)).first()
        group = Group(name=name, owner_id=ctx.author.id, session_id=session.session_id)
        db.add(group)
        db.commit()
        await ctx.send(f"Group {name} created successfully.")
        
    @groups_command_group.command(name="join", description="Open the group browser and join a group.")
    async def join_group(self, ctx):
        sessionSelectView = SessionSelectView(ctx)
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Please select a session to browse groups from.",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=sessionSelectEmbed, view=sessionSelectView)
        await sessionSelectView.wait()
        session = sessionSelectView.session
        session = db.query(Session).filter(Session.id == session).first()
        groups = db.query(Group).filter(Group.session_id == session.session_id).all()
        if len(groups) == 0:
            await ctx.send("No groups found.")
            return
        groupBrowseView = GroupBrowseView(groups)
        groupBrowseEmbed, groupBrowseView = groupBrowseView.update()
        await ctx.respond(embed=groupBrowseEmbed, view=groupBrowseView)
        await groupBrowseView.wait()
        if groupBrowseView.selected_group is None:
            await ctx.send("Cancelled.")
            return
        
        group = db.query(Group).filter(Group.id == int(groupBrowseView.selected_group)).first()
        group_join = GroupJoin(user_id=ctx.author.id, group_id=group.id)
        db.add(group_join)
        db.commit()
        await ctx.send(f"Joined group {group.name} successfully.")
        
    @groups_command_group.command(name="leave", description="Leave a group.")
    async def leave_group(self, ctx):
        selectSessionView = SessionSelectView(ctx)
        selectSessionEmbed = discord.Embed(
            title="Select a session",
            description="Please select a session to browse groups from.",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=selectSessionEmbed, view=selectSessionView)
        await selectSessionView.wait()
        session = selectSessionView.session
        session = db.query(Session).filter(Session.id == session).first()
        groups = db.query(Group).filter(Group.session_id == session.session_id).all()
        groupJoins = db.query(GroupJoin).filter(GroupJoin.user_id == ctx.author.id).all()
        if len(groupJoins) == 0:
            await ctx.send("You have not joined any groups.")
            return
        groupBrowseView = GroupBrowseView(groups)
        groupBrowseEmbed, groupBrowseView = groupBrowseView.update()
        await ctx.respond(embed=groupBrowseEmbed, view=groupBrowseView)
        await groupBrowseView.wait()
        if groupBrowseView.selected_group is None:
            await ctx.send("Cancelled.")
            return
        group = db.query(Group).filter(Group.id == int(groupBrowseView.selected_group)).first()
        group_join = db.query(GroupJoin).filter(GroupJoin.user_id == ctx.author.id, GroupJoin.group_id == group.id).first()
        db.delete(group_join)
        db.commit()
        await ctx.send(f"Left group {group.name} successfully")
        
    @groups_command_group.command(name="joined", description="Leave a group.")
    async def joined_groups(self, ctx):
        selectSessionView = SessionSelectView(ctx)
        selectSessionEmbed = discord.Embed(
            title="Select a session",
            description="Please select a session to browse groups from.",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=selectSessionEmbed, view=selectSessionView)
        await selectSessionView.wait()
        session = selectSessionView.session
        session = db.query(Session).filter(Session.id == session).first()
        groups = db.query(Group).filter(Group.session_id == session.session_id).all()
        joinedGroupsEmbed = discord.Embed(
            title="Joined groups",
            description="These are all the groups you have joined.",
            color=discord.Color.blue()
        )
        for group in groups[:25]:
            joinedGroupsEmbed.add_field(
                name=group.name,
                value=f"Owner: <@{group.owner_id}>"
            )
        await ctx.send(embed=joinedGroupsEmbed)
            
def setup(bot):
    bot.add_cog(groupsCog(bot))