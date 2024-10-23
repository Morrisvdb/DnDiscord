from math import e
import discord, datetime
from discord.ext import commands, tasks
from models import Guild, Session, SessionSignup, setup_required
from ui.SessionModals import SessionSelectView, PresenceView, ViewPresenceView, DayTimeView
from ui.SystemModals import ConfirmView
from __init__ import db

class SessionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_sessions.start()
    
    sessioncommands_group = discord.SlashCommandGroup(name='session', description='Session commands for the bot.')
    
    @sessioncommands_group.command(name="create")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @setup_required()
    @commands.has_permissions(administrator=True)
    async def create(self, ctx, name: str):
        session = db.query(Session).filter(Session.name == name).first()
        if session is not None:
            await ctx.respond("A session with that name already exists.", ephemeral=True)
            return
        
        dayTimeView = DayTimeView(ctx)
        dayTimeEmbed = dayTimeView.generate_embed()
        
        msg = await ctx.respond(embed=dayTimeEmbed, view=dayTimeView, ephemeral=True)
        await dayTimeView.wait()
        
        if dayTimeView.day is None or dayTimeView.time is None:
            await ctx.respond("No day or time selected.")
            return
        
        await msg.edit(content=f"Session {name} created successfully.", view=None)
        
        session = Session(name=name, guild_id=ctx.guild.id, is_active=True, day=dayTimeView.day, time=dayTimeView.time)
        db.add(session)
        db.commit()
        
    @sessioncommands_group.command(name="delete")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @setup_required()        
    async def delete(self, ctx):
        sessionSelectView = SessionSelectView(ctx)
        
        msg = await ctx.respond("Select a session.", view=sessionSelectView, ephemeral=True)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await msg.edit("No session selected.")
            return
        
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        if session is None:
            await msg.edit("No session found.")
            return
        
        confirmEmbed = discord.Embed(
            title="Delete Session",
            description=f"Are you sure you want to delete the session {session.name}?",
            color=discord.Color.red()
        )
        confirmView = ConfirmView()
        msg = await ctx.respond(embed=confirmEmbed, view=confirmView, ephemeral=True)
        
        await confirmView.wait()
        if not confirmView.choice:
            canceledEmbed = discord.Embed(
                title="Canceled",
                description="Session deletion canceled. \n No changes were made.",
                color=discord.Color.green()
            )
            await msg.edit(embed=canceledEmbed, view=None)
            return
        
        db.delete(session)
        db.commit()
        
        await ctx.respond(f"Session {session.name} deleted successfully.", ephemeral=True)
            
    @sessioncommands_group.command(name="presence")
    @setup_required()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def presence(self, ctx):
        sessionSelectView = SessionSelectView(ctx)
        
        msg = await ctx.respond("Select a session to manage your presence.", view=sessionSelectView, ephemeral=True)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await msg.edit("No session selected.")
            return
        
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        if session is None:
            await msg.edit("No session found.")
            return
        
        presenceView = PresenceView(ctx, session)
        presenceEmbed = discord.Embed(
            title="Select your presence",
            description="Select your presence for the session. \n Selecting absent will automatically cancel all groups you own.",
            color=discord.Color.blue()
        )
        await msg.edit(view=presenceView, embed=presenceEmbed)
        await presenceView.wait()
        
        if presenceView.state is None:
            await msg.edit("No state selected.")
            return
        
        signup = db.query(SessionSignup).filter(SessionSignup.user_id == ctx.author.id, SessionSignup.session_id == session.id).first()
        if signup is None:
            signup = SessionSignup(user_id=ctx.author.id, session_id=session.id)
        
        signup.state = presenceView.state
        db.add(signup)
        db.commit()
        
        await ctx.respond(f"Your presence for session {session.name} has been set to {'Present' if presenceView.state else 'Absent'}.", ephemeral=True)
        
    @sessioncommands_group.command(name="list", description="List all people of a session.")
    @setup_required()
    @commands.guild_only()
    async def list(self, ctx):
        sessionSelectView = SessionSelectView(ctx)
        
        await ctx.respond("Select a session to list all participants.", view=sessionSelectView)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await ctx.respond("No session selected.")
            return
        
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        if session is None:
            await ctx.respond("No session found.")
            return
        
        signups = db.query(SessionSignup).filter(SessionSignup.session_id == session.id).all()
        viewPresenceView = ViewPresenceView(ctx, signups=signups, session=session)
        viewPresenceEmbed = viewPresenceView.generate_embed()
        await ctx.respond(embed=viewPresenceEmbed, view=viewPresenceView)
        await viewPresenceView.wait()

    @sessioncommands_group.command(name="default-signup", description="Set your default signup state for a session.")
    @commands.guild_only()
    @setup_required()
    async def default_signup(self, ctx):
        sessionSelectView = SessionSelectView(ctx)
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to set your default signup state.",
            color=discord.Color.blue()
        )
        msg = await ctx.respond(embed=sessionSelectEmbed, view=sessionSelectView, ephemeral=True)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await ctx.respond("No session selected.")
            return
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        
        if session is None:
            await ctx.respond("No session found.")
            return
        
        presenceView = PresenceView(ctx, session)
        presenceEmbed = discord.Embed(
            title="Select a default signup state",
            description="Select a default signup state for the session.",
            color=discord.Color.blue()
        )
        await msg.edit(embed=presenceEmbed, view=presenceView)
        await presenceView.wait()
        if presenceView.state is None:
            await ctx.respond("No state selected.")
            return
        
        signup = db.query(SessionSignup).filter_by(user_id=ctx.author.id, session_id=session.id).first()
        if signup is None:
            signup = SessionSignup(user_id=ctx.author.id, session_id=session.id)
        
        signup.standard = presenceView.state
        db.add(signup)
        db.commit()
        
        completeEmbed = discord.Embed(
            title="Default Signup State Set",
            description=f"Default signup state for session {session.name} set to {'Present' if presenceView.state else 'Absent'}.",
            color=discord.Color.green()
        )
        await msg.edit(embed=completeEmbed, view=None)        
        
    @sessioncommands_group.command(name="default-remove", description="Remove your default signup state for a session.")
    @commands.guild_only()
    @setup_required()
    async def default_remove(self, ctx):
        sessionSelectView = SessionSelectView(ctx)
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to remove your default signup state.",
            color=discord.Color.blue()
        )
        msg = await ctx.respond(embed=sessionSelectEmbed, view=sessionSelectView, ephemeral=True)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await ctx.respond("No session selected.")
            return
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        
        if session is None:
            await ctx.respond("No session found.")
            return
        
        signup = db.query(SessionSignup).filter_by(user_id=ctx.author.id, session_id=session.id).first()
        if signup is None:
            await ctx.respond("No default signup state found.")
            return
        
        signup.standard = None
        db.add(signup)
        db.commit()
        
        await msg.edit(content=f"Default signup state for session {session.name} removed successfully.", view=None, embed=None)

    @sessioncommands_group.command(name="default-see", description="Get your default state for a session.")
    @commands.guild_only()
    @setup_required()
    async def default_see(self, ctx):
        sessionSelectView = SessionSelectView(ctx)
        sessionSelectEmbed = discord.Embed(
            title="Select a session",
            description="Select a session to see your default signup state.",
            color=discord.Color.blue()
        )
        msg = await ctx.respond(embed=sessionSelectEmbed, view=sessionSelectView, ephemeral=True)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await ctx.respond("No session selected.")
            return
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        
        if session is None:
            await msg.edit(content="No session found.", embed=None, view=None)
            return
        
        signup = db.query(SessionSignup).filter_by(user_id=ctx.author.id, session_id=session.id).first()
        if signup is None or signup.standard is None:
            await msg.edit(content="No default signup state found.", embed=None, view=None)
            return
        
        await msg.edit(content=f"Your default signup state for session {session.name} is {'Present' if signup.standard else 'Absent'}.", embed=None, view=None)

    @sessioncommands_group.command(name="deactivate", description="Deactivate a session.")
    @commands.guild_only()
    @setup_required()
    @commands.has_permissions(administrator=True)
    async def deactivate(self, ctx):
        sessionSelectView = SessionSelectView(ctx)
        
        await ctx.respond("Select a session to deactivate.", view=sessionSelectView)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await ctx.respond("No session selected.")
            return
        
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        if session is None:
            await ctx.respond("No session found.")
            return
        
        if session.is_active is False:
            await ctx.respond("Session is already deactivated.")
            return
                
        session.is_active = False
        db.add(session)
        db.commit()
        
        await ctx.respond(f"Session {session.name} deactivated successfully.", ephemeral=True)

    @sessioncommands_group.command(name="activate", description="Activate a session.")
    @commands.guild_only()
    @setup_required()
    @commands.has_permissions(administrator=True)
    async def activate(self, ctx):
        sessionSelectView = SessionSelectView(ctx)
        
        await ctx.respond("Select a session to activate.", view=sessionSelectView)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await ctx.respond("No session selected.")
            return
        
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        if session is None:
            await ctx.respond("No session found.")
            return
        
        if session.is_active is True:
            await ctx.respond("Session is already activated.")
            return
                
        session.is_active = True
        db.add(session)
        db.commit()
        
        await ctx.respond(f"Session {session.name} activated successfully.", ephemeral=True)

    @sessioncommands_group.command(name='unplay', description='Reset the played status of a session. (used for when it probarbly decides to break)')
    @commands.guild_only()
    @setup_required()
    @commands.has_permissions(administrator=True)
    async def unplay(self, ctx):
        sessionSelectView = SessionSelectView(ctx)
        
        await ctx.respond("Select a session to unplay.", view=sessionSelectView)
        await sessionSelectView.wait()
        if sessionSelectView.session is None:
            await ctx.respond("No session selected.")
            return
        
        session = db.query(Session).filter(Session.id == sessionSelectView.session).first()
        if session is None:
            await ctx.respond("No session found.")
            return
        
        session.played_today = False
        db.add(session)
        db.commit()
        
        await ctx.respond(f"Session {session.name} unplayed successfully.", ephemeral=True)

    @tasks.loop(seconds=10)
    async def check_sessions(self):
        """
        Checks if sessions are due and handles them accoridingly
        """
        sessions = db.query(Session).all()
        for session in sessions:
            # ------- Auto cancel groups -------
            for group in db.query(Group).filter(Group.session_id == session.id).all():
                if db.query(SessionSignup).filter_by(user_id = group.owner_id, session_id = session.id).first().state is False:
                    group.canceled = True
                    db.add(group)
                    db.commit()
                    
                elif db.query(SessionSignup).filter_by(user_id = group.owner_id, session_id = session.id).first().state is True:
                    group.cancelled = False
                    db.delete(group)
                    db.commit()
            
            
            for signup in db.query(SessionSignup).filter(SessionSignup.session_id == session.id).all():
                if signup.standard is not None and signup.state is None:
                    signup.state = signup.standard
                    db.add(signup)
                    db.commit()
            
            if session.is_active and not session.played_today:
                today = datetime.datetime.today()
                if today.strftime("%A").lower() == session.day: # Checks if the day is today
                    if today.time() >= session.time: # Checks if the time is past the session time
                        # ------------------ Playing Session ------------------
                        signups = db.query(SessionSignup).filter(SessionSignup.session_id == session.id).all()
                        session.played_today = True
                        db.add(session)
                        
                        for signup in signups:
                            # Clear signup state
                            if signup.standard is not None:
                                signup.state = None
                                db.add(signup)
                            else:
                                db.delete(signup)
                        
                        db.commit()
                else:
                    # Unsets played_today if the day is not today
                    if session.played_today:
                        session.played_today = False
                        db.add(session)
                        db.commit()
            else:
                pass

def setup(bot):
    bot.add_cog(SessionCog(bot))