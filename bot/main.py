from __init__ import bot, db
from models import Guild
from config import Config
import functools

bot.remove_command('help')
bot.load_extension('cogs.SystemCog')
bot.load_extension('cogs.SessionCog')
bot.load_extension('cogs.HelpCog')
bot.load_extension('cogs.RolesCog')
bot.load_extension('cogs.GroupsCog')

@bot.event
async def on_ready():
    bot.remove_command('help')
    print('------')
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('------')
    
    

bot.run(Config.TOKEN)