from __init__ import bot, db
from models import Guild
from config import Config
import functools
  
bot.load_extension('cogs.SystemCog')
bot.load_extension('cogs.SessionCog')

@bot.event
async def on_ready():
    print('------')
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('------')
    
    

bot.run(Config.TOKEN)