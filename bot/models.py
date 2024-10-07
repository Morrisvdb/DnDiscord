from sqlalchemy import Column, Integer, String, Boolean, VARCHAR, Time
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
    roles_select_channel = Column(VARCHAR(255), nullable=True)
    is_set_up = Column(Boolean)
    
    def __repr__(self):
        return f'<Guild {self.guild_id}>'   
    
class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(VARCHAR(255), unique=True)
    guild_id = Column(VARCHAR(255))
    time = Column(Time())
    day = Column(String(255)) # Any of: monday, tuesday, wednesday, thursday, friday, saturday, sunday
    name = Column(String(255))
    is_active = Column(Boolean)
    played_today = Column(Boolean)
    
    def __repr__(self):
        return f'<Session {self.name}>'

class SessionSignup(Base):
    __tablename__ = 'session_signups'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(VARCHAR(255))
    session_id = Column(VARCHAR(255))
    state = Column(Boolean)
    standard = Column(Boolean, default=None)
    
    def __repr__(self):
        return f'<SessionSignup {self.user_id} for {self.session_id}>'

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    role_id = Column(VARCHAR(255), unique=True)
    guild_id = Column(VARCHAR(255))
    
    def __repr__(self):
        return f'<Role {self.role_id}>'
    
class RoleMessages(Base):
    __tablename__ = 'role_messages'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(VARCHAR(255), unique=True)
    guild_id = Column(VARCHAR(255))
    channel_id = Column(VARCHAR(255))
    
    def __repr__(self):
        return f'<RoleMessages {self.name}>'

Base.metadata.create_all(engine)
