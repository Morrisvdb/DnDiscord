from sqlalchemy import Column, Integer, String, Boolean, VARCHAR
from __init__ import Base, engine, db
from discord.ext import commands


def setup_required():
    async def predicate(ctx):
        guild = db.query(Guild).filter_by(guild_id=ctx.guild.id).first()
        if guild is None:
            await ctx.respond("Set up incomplete")
            return False
        if guild.is_set_up is False:
            await ctx.respond("Set up incomplete")
            return False
        return True
    return commands.check(predicate)

class Guild(Base):
    __tablename__ = 'guilds'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(VARCHAR(255), unique=True)
    joinmsg = Column(String(255), default='Welcome {user} to {guild}!')
    leavemsg = Column(String(255), default='Goodbye {user}!')
    autorole_id = Column(VARCHAR(255))
    updates_channel_id = Column(VARCHAR(255))
    announce_channel_id = Column(VARCHAR(255))
    is_set_up = Column(Boolean)
    
    def __repr__(self):
        return f'<Guild {self.guild_id}>'   
    

Base.metadata.create_all(engine)
