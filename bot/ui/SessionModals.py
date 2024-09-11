import discord
from __init__ import db
from models import Session
from ui.SystemModals import EnterStringModal
from function import parse_time

class SessionSelectView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

        self.session = None
        
        sessions = db.query(Session).filter(Session.guild_id == ctx.guild.id).all()
        select_sessions = []
        for session in sessions:
            select_sessions.append(discord.SelectOption(label=session.name, value=str(session.id)))
            
        if len(select_sessions) == 0:
            select_sessions = [discord.SelectOption(label="No Sessions Found", value="none")]
        
        self.session_select.options = select_sessions
        
    @discord.ui.select(placeholder="Select a Session", options=[discord.SelectOption(label="No Sessions Found", value="none")])
    async def session_select(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.session = select.values[0]
        await interaction.response.defer()
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.session = None
        self.stop()
        await interaction.response.edit_message(view=None)
        
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.stop()
        await interaction.response.edit_message(view=None)
        
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.respond("Bad hooman, this is not for you!")
            return False
        return True
 
class PresenceView(discord.ui.View):
    def __init__(self, ctx, session):
        super().__init__()
        self.ctx = ctx
        self.session = session
        self.state = None 
        
    @discord.ui.button(label="Present", style=discord.ButtonStyle.success)
    async def present_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.state = True
        await interaction.response.defer()
        # await interaction.respond("Your presence has been set to Present.", ephemeral=True)
        self.stop()
        
    @discord.ui.button(label="Absent", style=discord.ButtonStyle.danger)
    async def absent_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.state = False
        await interaction.response.defer()
        # await interaction.respond("Your presence has been set to Absent.", ephemeral=True)
        self.stop()
        
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.respond("Bad hooman, this is not for you!")
            return False
        return True
    
class ViewPresenceView(discord.ui.View):
    def __init__(self, ctx, signups, session):
        super().__init__()
        self.ctx = ctx
        self.session = session
        self.signups = signups
        self.page = 0        
    
    def generate_embed(self):
        newEmbed = discord.Embed(
            title=f"Participants of {self.session.name}", 
            color=discord.Color.green()            
            )
        for signup in self.signups[self.page*5:self.page*5+5]:
            user = self.ctx.guild.get_member(int(signup.user_id))
            value = ": " + ("Present" if signup.state else "Absent")
            if signup.standard is not None:
                standard = " - Standard: **" + ("Present" if signup.standard else "Absent") + "**"
            else:
                standard = "- Standard: **N/A**"
            newEmbed.add_field(name=user.display_name + value, value=standard)
            
        newEmbed.set_footer(text=f"Page {self.page+1}/{len(self.signups)//5+1}")
        
        return newEmbed

            
        
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page != 0:
            self.page -= 1
        newEmbed = self.generate_embed()
        await interaction.response.edit_message(view=self, embed=newEmbed)
        
    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page*5+5 < len(self.signups):
            self.page += 1
        newEmbed = self.generate_embed()
        await interaction.response.edit_message(view=self, embed=newEmbed)

class DayTimeView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.day = None
        self.time = None
        self.stopped = False
        
    def generate_embed(self):
        if self.stopped:
            newEmbed = discord.Embed(
                title="Create a new session",
                description="Session creation has ended."
                )
            return newEmbed
        newEmbed = discord.Embed(
            title="Create a new session",
            description="Please select a day and time for the session.",
            color=discord.Color.green()
        )
        if self.day is not None:
            newEmbed.add_field(name="Day", value=self.day)
        if self.time is not None:
            newEmbed.add_field(name="Time", value=f"{self.time.strftime('%H:%M')}")
        return newEmbed
        
    @discord.ui.select(placeholder="Select a Day", options=[discord.SelectOption(label="Monday", value="monday"), discord.SelectOption(label="Tuesday", value="tuesday"), discord.SelectOption(label="Wednesday", value="wednesday"), discord.SelectOption(label="Thursday", value="thursday"), discord.SelectOption(label="Friday", value="friday"), discord.SelectOption(label="Saturday", value="saturday"), discord.SelectOption(label="Sunday", value="sunday")])
    async def day_select(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.day = select.values[0]
        await interaction.response.edit_message(embed=self.generate_embed())
        
        
    @discord.ui.button(label="Select Time", style=discord.ButtonStyle.primary)
    async def select_time_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = EnterStringModal(title="Format (HH:MM) 24 hour time.", fieldName="Time")
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        time = modal.result
        time = parse_time(time)
        if time == None:
            modal.stop()
            await self.ctx.send("Invalid time format. Please try again.")
            return
        self.time = time        
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.day = None
        self.time = None
        self.stopped = True
        self.stop()
        embed = self.generate_embed()
        await interaction.response.edit_message(view=None, embed=embed)
        
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.stop()
        self.stopped = True
        embed = self.generate_embed()
        await interaction.response.edit_message(view=None, embed=embed)
        
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.respond("Bad hooman, this is not for you!")
            return False
        return True