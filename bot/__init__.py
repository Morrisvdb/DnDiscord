import discord, sqlalchemy, time
from discord.ext import commands
from config import Config

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

bot = commands.Bot(command_prefix=Config.prefix)

for i in range(5):
    try:
        engine = create_engine(Config.db_url)
        Base = declarative_base()
        Session = sessionmaker(bind=engine)
        db = Session()
        break
        
    except Exception as e:
        print(f"Failed to connect to database. Retrying in 5 seconds. ({i+1}/5)")
        time.sleep(2)
        

