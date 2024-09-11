import os, discord
from discord.ext import commands
from ui.HelpModals import HelpView

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # helpcommands_group = discord.SlashCommandGroup(name='help', description='Help commands for the bot.', guild_ids=[977513866097479760])
    
    @discord.slash_command(name="help", guild_ids=[977513866097479760])
    # @helpcommands_group.command()
    async def help(self, ctx):
        """Shows the help menu for the bot.
        
        Args:
            ctx (discord.ApplicationContext)
        """
        help_files = []
        for file in os.listdir('bot/help'):
            if file.endswith('.json'):
                help_files.append(file)
        
        view = HelpView(ctx, files = help_files)
        await ctx.respond(embed=view.generate_embed(), view=view)
        
        
    @discord.slash_command(name="test", guild_ids=[977513866097479760])
    async def test(self, ctx):
        print(ctx.author.guild_permissions)

def setup(bot):
    bot.add_cog(HelpCog(bot))