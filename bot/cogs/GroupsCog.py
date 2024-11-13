from operator import is_
from select import select
from tokenize import group
import discord
from discord.ext import commands
from sqlalchemy import desc
from ui.SessionModals import SessionSelectView
from ui.GroupModals import GroupBrowseView, GroupSelectView, GroupEditView, ViewInvitesView, GroupsViewView
from models import Session, Group, GroupJoin, Guild
from __init__ import db


class groupsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    groups_command_group = discord.SlashCommandGroup(name="group", help="Group management commands.", guild_ids=[977513866097479760])
    
    @groups_command_group.command(name="create", description="Create a new group.")
    async def group_create(self, ctx, name, description: discord.Option(str, min=4, max=1023, required=False), private: bool = False):
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
        if db.query(Group).filter(Group.name == name, Group.session_id == session.id).first():
            await msg.edit(content="A group with that name already exists.", view=None, embed=None)
            return
        
        guild = db.query(Guild).filter_by(guild_id=ctx.guild.id).first()
        groupChannelCategory = discord.utils.get(ctx.guild.categories, id=int(guild.groups_channel_category_id))
        groupChannel = await groupChannelCategory.create_text_channel(name=name)
        groupRole = await ctx.guild.create_role(name=name)
        await groupChannel.set_permissions(groupRole, view_channel=True)
        
        
        group = Group(name=name, owner_id=ctx.author.id, session_id=session.id, private=private, role_id=groupRole.id, channel_id=groupChannel.id)
        db.add(group)
        db.commit()
        
        await ctx.author.add_roles(groupRole)
        
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
        
        groupRole = ctx.guild.get_role(int(group.role_id))
        groupChannel = ctx.guild.get_channel(int(group.channel_id))

        try:
            await groupRole.delete()
        except AttributeError:
            pass
        try:
            await groupChannel.delete()
        except AttributeError:
            pass
        
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
        
        groups = db.query(Group).filter(Group.session_id == session.id, Group.private == False).all()
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
        groupRole = ctx.guild.get_role(int(group.role_id))
        await ctx.author.add_roles(groupRole)
        
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
        await msg.edit(embed=groupSelectEmbed, view=groupSelectView)
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
        
        groupRole = await ctx.guild.fetch_role(int(group.role_id))
        await ctx.author.remove_roles(groupRole)
        
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
        if groupEditView.name_is_edited or groupEditView.description_is_edited or groupEditView.private_is_edited:
            if groupEditView.name_is_edited and groupEditView.name and groupEditView.private_is_edited is not None:
                group.name = groupEditView.name
            if groupEditView.description_is_edited and groupEditView.description is not None:
                group.description = groupEditView.description
            if groupEditView.private_is_edited and groupEditView.private is not None:
                group.private = groupEditView.private
            db.add(group)
            db.commit()
            change = True
        
        if change:
            await msg.edit(content="Group changes have been registered and should update soon!", view=None, embed=None)
        else:
            await msg.edit(content="No changes were made, nothing happened!", view=None, embed=None)
            
    @groups_command_group.command(name="transfer", description="Transfer ownership of a group.")
    async def group_transfer(self, ctx, user: discord.Member):
        if user == ctx.author:
            await ctx.respond("You silly goose! You can't transfer the group to yourself!", ephemeral=True)
            return
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to pick a group for.",
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
            title="Select a group",
            description="Select a group.",
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
        
        group.owner_id = user.id
        db.add(group)
        db.commit()
        
    @groups_command_group.command(name="kick", description="Kick a user from a group.")
    async def group_kick(self, ctx, user: discord.Member):
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to pick a group for.",
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
            title="Select a group",
            description="Select a group.",
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
        
        groupJoin = db.query(GroupJoin).filter(GroupJoin.user_id == user.id, GroupJoin.group_id == group.id).first()
        if groupJoin is None:
            await msg.edit(content="User is not in this group.", view=None, embed=None)
            return
        
        groupRole = ctx.guild.get_role(int(group.role_id))
        await ctx.author.remove_roles([groupRole])

        
        db.delete(groupJoin)
        db.commit()
        
        successEmbed = discord.Embed(
            title="User kicked",
            description=f"{user.mention} has been kicked from group `{group.name}`.",
            color=discord.Color.green()
        )
        await msg.edit(embed=successEmbed, view=None)
        
    @groups_command_group.command(name="invite", description="Invite a user to a group.")
    async def group_invite(self, ctx, user: discord.Member):
        if user == ctx.author:
            await ctx.respond("You silly goose! You can't invite yourself to a group!", ephemeral=True)
            return
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to pick a group for.",
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
            title="Select a group",
            description="Select a group.",
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
        
        groupJoin = db.query(GroupJoin).filter(GroupJoin.user_id == user.id, GroupJoin.group_id == group.id).first()
        if groupJoin is not None:
            await msg.edit(content="User is already in this group.", view=None, embed=None)
            return
        
        groupInvite = db.query(GroupJoin).filter(GroupJoin.user_id == user.id, GroupJoin.group_id == group.id, GroupJoin.is_invite == True).first()
        if groupInvite is not None:
            await msg.edit(content="User already has an invite to this group.", view=None, embed=None)
            return
        
        groupJoin = GroupJoin(user_id=user.id, group_id=group.id, is_invite=True)
        db.add(groupJoin)
        db.commit()
        
        dm_channel = await user.create_dm()
        
        inviteEmbed = discord.Embed(
            title=f"Group invite from {ctx.author.name}",
            description=f"""
            <@{ctx.author.id}> has invited you to join their group in {ctx.guild.name}.
            To accept this invite, go to the server and join the group manually.
            """,
            color=discord.Color.blue()
        )
        await dm_channel.send(embed=inviteEmbed)        
        
        successEmbed = discord.Embed(
            title="User invited",
            description=f"{user.mention} has been invited to group `{group.name}`.",
            color=discord.Color.green()
        )
        await msg.edit(embed=successEmbed, view=None)
        
    @groups_command_group.command(name="invites-list", description="Accept a group invite.")
    async def group_accept(self, ctx):
        invites_list = db.query(GroupJoin).filter(GroupJoin.user_id == ctx.author.id, GroupJoin.is_invite == True).all()
        if len(invites_list) == 0:
            await ctx.respond("No invites found.", ephemeral=True)
            return
        viewInvitesView = ViewInvitesView(invites_list)
        viewInvitesEmbed = await viewInvitesView.update()
        msg = await ctx.respond(embed=viewInvitesEmbed, view=viewInvitesView, ephemeral=True)
        await viewInvitesView.wait()
        if viewInvitesView.selected_invite is None:
            await msg.edit(content="No invite selected.", view=None, embed=None)
            return
        
        invite = db.query(GroupJoin).filter(GroupJoin.id == viewInvitesView.selected_invite).first()
        if invite is None:
            await msg.edit(content="Invalid invite selected.", view=None, embed=None)
            return
        
        if viewInvitesView.action == "delete":
            db.delete(invite)
            group_name = db.query(Group).filter(Group.id == invite.group_id).first().name
            successEmbed = discord.Embed(
                title="Invite deleted",
                description=f"Invite to {group_name} has been deleted.",
                color=discord.Color.green()
            )
        
        if viewInvitesView.action == "accept":        
            invite.is_invite = False
            db.add(invite)
            group_name = db.query(Group).filter(Group.id == invite.group_id).first().name
            successEmbed = discord.Embed(
                title="Invite accepted",
                description=f"You have accepted the invite to group `{group_name}`.",
                color=discord.Color.green()
            )
        db.commit()
        
        
        await msg.edit(embed=successEmbed, view=None)
        
    @groups_command_group.command(name='list', description="List groups.")
    async def group_list(self, ctx):
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to list groups for.",
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
        
        groupListView = GroupsViewView(ctx=ctx, groups=groups)
        groupListEmbed = await groupListView.update()
        await msg.edit(embed=groupListEmbed, view=groupListView)
        
    @groups_command_group.command(name='cancel', description="Cancel a group, meaning that you will be absent.")
    async def group_cancel(self, ctx):
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to cancel a group for.",
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
        
        groupSelectView = GroupSelectView(groups)
        groupSelectEmbed = discord.Embed(
            title="Select a group to cancel",
            description="Select a group to cancel.",
            color=discord.Color.blue()
        )
        
        await msg.edit(embed=groupSelectEmbed, view=groupSelectView)
        await groupSelectView.wait()
        
        if groupSelectView.selected_group is None:
            await msg.edit(content="No group selected.", view=None, embed=None)
            return
        
        group = db.query(Group).filter(Group.id == groupSelectView.selected_group).first()
        if group is None:
            await msg.edit(content="Invalid group selected.", view=None, embed=None)
            return
        
        group.canceled = True
        db.add(group)
        db.commit()
        
        successEmbed = discord.Embed(
            title="Group canceled",
            description=f"Group `{group.name}` has been canceled.",
            color=discord.Color.green()
        )
        await msg.edit(embed=successEmbed, view=None)
        
    @groups_command_group.command(name="uncancel", description="Uncancel a group, meaning that you will be present.")
    async def group_uncancel(self, ctx):
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to uncancel a group for.",
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
        
        groupSelectView = GroupSelectView(groups)
        groupSelectEmbed = discord.Embed(
            title="Select a group to uncancel",
            description="Select a group to uncancel.",
            color=discord.Color.blue()
        )
        
        await msg.edit(embed=groupSelectEmbed, view=groupSelectView)
        await groupSelectView.wait()
        
        if groupSelectView.selected_group is None:
            await msg.edit(content="No group selected.", view=None, embed=None)
            return
        
        group = db.query(Group).filter(Group.id == groupSelectView.selected_group).first()
        if group is None:
            await msg.edit(content="Invalid group selected.", view=None, embed=None)
            return
        
        group.canceled = False
        db.add(group)
        db.commit()
        
        successEmbed = discord.Embed(
            title="Group canceled",
            description=f"Group `{group.name}` has been canceled.",
            color=discord.Color.green()
        )
        await msg.edit(embed=successEmbed, view=None)
       
    # @groups_command_group.command(name='toggle-group-channels', description="toggle wether each group gets their own channel and role")
    # async def group_toggle_group_channels(self, ctx, category: discord.CategoryChannel):
    #     guild = db.query(Guild).filter_by(guild_id = ctx.guild.id).first()
    #     guild.groups_channel_category_id = category.id if guild.groups_channel_category_id is None else None
    #     db.add(guild)
    #     db.commit()
    #     successEmbed = discord.Embed(
    #         title="Group channels toggled",
    #         description=f"Group channels have been {"enabled" if guild.groups_channel_category_id is not None else "disabled"} in category {category.name}.",
    #         color=discord.Color.green()
    #     )
    #     await ctx.respond(embed=successEmbed, ephemeral=True)
        
def setup(bot):
    bot.add_cog(groupsCog(bot))