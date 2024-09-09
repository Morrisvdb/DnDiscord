import discord
from discord.ext import commands
from models import Guild, setup_required
from ui.SystemModals import SetupView
from __init__ import db

class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        setup_channel = guild.safety_alerts_channel_id
        setupEmbed = discord.Embed(
            title="Hello!",
            description="Thanks for inviting me to your server! To get started, please run the `/system setup` command to configure the bot.",
            color=discord.Color.green()
        )
        await setup_channel.send(embed=setupEmbed)
    
    
    systemcommands_group = discord.SlashCommandGroup(name='system', description='System commands for the bot.', guild_ids=[977513866097479760])
    
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
        await ctx.respond(embed=setupEmbed, view=setupView)
    
        await setupView.wait()
        if setupView.default_channel is None or setupView.default_role is None:
            await ctx.respond("Setup cancelled.", ephemeral=True)
            return
        
        guild = db.query(Guild).filter(Guild.guild_id == ctx.guild.id).first()
        if guild is None:
            guild = Guild(guild_id=ctx.guild.id)
        
        guild.autorole_id = setupView.default_role
        guild.announce_channel_id = setupView.default_channel
        guild.updates_channel_id = setupView.updates_channel
        guild.is_set_up = True
        
        db.add(guild)
        db.commit()

def setup(bot):
    bot.add_cog(SystemCog(bot))