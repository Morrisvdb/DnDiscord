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
    
    @systemcommands_group.command()
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
        if setupView.user_updates_channel is None or setupView.default_role is None or setupView.admin_updates_channel is None:
            await ctx.respond("Setup cancelled.", ephemeral=True)
            return
        
        guild = db.query(Guild).filter(Guild.guild_id == ctx.guild.id).first()
        if guild is None:
            guild = Guild(guild_id=ctx.guild.id)
        
        guild.autorole_id = setupView.default_role
        guild.announce_channel_id = setupView.user_updates_channel
        guild.updates_channel_id = setupView.admin_updates_channel
        guild.roles_select_channel = setupView.role_select_channel
        guild.is_set_up = True
        
        await msg.edit(embed=discord.Embed(title="Setup complete!", color=discord.Color.green()), view=None)
        
        db.add(guild)
        db.commit()

    @tasks.loop(seconds=10)
    async def update_channels(self):
        guilds = db.query(Guild).filter_by(is_set_up=True).all()
        for guild in guilds:
            guild = await self.bot.fetch_guild(guild.guild_id)
            if guild is None:
                continue
            
            guildobj = db.query(Guild).filter(Guild.guild_id == guild.id).first()
                
            for member in guild.members:
                if guild.get_role(guildobj.autorole_id) not in member.roles:
                    await member.add_roles(guild.get_role(guildobj.autorole_id))
            
            role_channel = await guild.fetch_channel(guildobj.roles_select_channel)
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
