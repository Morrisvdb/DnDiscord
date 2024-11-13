from os import system
import discord
from discord.ext import commands, tasks
from models import Guild, setup_required, RoleMessages, Role
from ui.SystemModals import SetupView
from ui.RoleModals import RoleSelectView
from __init__ import db

class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_channels.start()
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        setup_channel = guild.safety_alerts_channel_id
        setupEmbed = discord.Embed(
            title="Hello!",
            description="Thanks for inviting me to your server! To get started, please run the `/system setup` command to configure the bot.",
            color=discord.Color.green()
        )
        await setup_channel.send(embed=setupEmbed)
    
    systemcommands_group = discord.SlashCommandGroup(name='system', description='System commands for the bot.')
    
    @systemcommands_group.command(name='setup', description='Set up the bot for the first time.')
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        """Helps an admin set up the bot for the first time.

        Args:
            ctx (discord.ApplicationContext)
        """
        setupEmbed = discord.Embed(
            title="Setup",
            description="This command will walk you through the initial setup of the bot.",
            color=discord.Color.green()
        )
        setupView = SetupView(ctx=ctx)
        msg = await ctx.respond(embed=setupEmbed, view=setupView)
    
        await setupView.wait()
        for item in setupView.to_configure.keys():
            if getattr(setupView, item) is None:
                await msg.edit(embed=discord.Embed(title="Setup cancelled.", color=discord.Color.red()), view=None)
                return
        
        guild = db.query(Guild).filter(Guild.guild_id == ctx.guild.id).first()
        if guild is None:
            guild = Guild(guild_id=ctx.guild.id)
        
        for item in setupView.to_configure.keys():
            setattr(guild, item, getattr(setupView, item))
        guild.is_set_up = True
        
        await msg.edit(embed=discord.Embed(title="Setup complete!", color=discord.Color.green()), view=None)
        
        db.add(guild)
        db.commit()

    @systemcommands_group.command(name='bug', description='Found a bug? Report it here!')
    async def system_bug(self, ctx):
        """Report a bug to the developers.

        Args:
            ctx (discord.ApplicationContext)
        """
        bugEmbed = discord.Embed(
            title="Report a bug",
            description="Found a bug? Report it on our GitHub page!",
            url="https://github.com/Morrisvdb/DnDiscord/issues"
        )
        await ctx.respond(embed=bugEmbed)

    @systemcommands_group.command(name='set-default-role', description='Set the default role for new members.')
    @setup_required()
    async def set_default_role(self, ctx, role: discord.Role):
        """Set the default role for new members. This role will be applied to all members when they join. Requires administrator permissions.

        Args:
            ctx (discord.ApplicationContext)
            role (discord.Role): The role to set as the default role.
        """
        guild = db.query(Guild).filter(Guild.guild_id == ctx.guild.id).first()
        
        guild.autorole_id = role.id
        
        db.add(guild)
        db.commit()
        
        await ctx.respond(f"Default role set to {role.mention}.", ephemeral=True)        

    @systemcommands_group.command(name='apply-default-roles', description='Apply the default roles to all members.')
    @setup_required()
    async def apply_default_roles(self, ctx):
        """Apply the default roles to all members.

        Args:
            ctx (discord.ApplicationContext)
        """
        guild = db.query(Guild).filter(Guild.guild_id == ctx.guild.id).first()
        role = ctx.guild.get_role(int(guild.autorole_id))
        
        if role is None:
            await ctx.respond("No default role set.", ephemeral=True)
            return
        
        for member in ctx.guild.members:
            if ctx.guild.get_role(guild.autorole_id) not in member.roles:
                try:
                    await member.add_roles(role)
                except discord.errors.Forbidden:
                    pass # Silently fail if the role is higher than the bot's role
        
        await ctx.respond("Default roles applied to all members.", ephemeral=True)

    @tasks.loop(seconds=10)
    async def update_channels(self):
        guilds = db.query(Guild).filter_by(is_set_up=True).all()
        for guild in guilds:
            guild = self.bot.get_guild(int(guild.guild_id))
            if guild is None:
                continue
            
            guildobj = db.query(Guild).filter(Guild.guild_id == guild.id).first()
            members = guild.members
            for member in members:
                if guild.get_role(int(guildobj.autorole_id)) not in member.roles:
                    try:
                        await member.add_roles(guild.get_role(int(guildobj.autorole_id)))
                    except discord.errors.Forbidden:
                        pass # Silently fail if the role is higher than the bot's role
            
            role_channel = await guild.fetch_channel(int(guildobj.roles_select_channel))
            if role_channel is not None:
                roles_models = db.query(Role).filter_by(guild_id=guild.id).all()
                roles = []
                for role in roles_models:
                    roles.append(guild.get_role(int(role.role_id)))
                if len(roles) == 0:
                    continue
                
                roleMessage = db.query(RoleMessages).filter(RoleMessages.guild_id == guild.id).first()
                roleSelectView = RoleSelectView(roles=roles)
                if roleMessage is not None:
                    if roleMessage.message_id is None:
                        msg = await role_channel.send("Select your roles!", view=roleSelectView)
                        roleMessage.message_id = msg.id
                        db.add(roleMessage)
                    try:
                        message = await role_channel.fetch_message(roleMessage.message_id)
                    except discord.errors.NotFound:
                        roleMessage.message_id = None
                        db.add(roleMessage)
                        db.commit()
                        message = None
                    if message is not None:
                        await message.edit(view=roleSelectView)
                    else:
                        roleMessage.message_id = None
                        db.add(roleMessage)
                        db.commit()
                else:
                    roleMessage = RoleMessages(guild_id=guild.id, message_id=None)
                    msg = await role_channel.send("Select your roles!", view=roleSelectView)
                    roleMessage.message_id = msg.id
                    db.add(roleMessage)
                    db.commit()
                
            db.commit()

    
def setup(bot):
    bot.add_cog(SystemCog(bot))
