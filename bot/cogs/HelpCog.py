import os, discord
from discord.ext import commands
from ui.HelpModals import HelpView

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    
    @discord.slash_command(name="help")
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

def setup(bot):
    bot.add_cog(HelpCog(bot))