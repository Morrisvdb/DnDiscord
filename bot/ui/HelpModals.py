import discord, json
from discord.ext import commands

class HelpView(discord.ui.View):
    # TODO: Make this fully procedurally generated
    def __init__(self, ctx, files = []):
        super().__init__()
        self.ctx = ctx
        self.current_category = None
        self.is_home = True
        self.files = files

    def generate_embed(self):
        if self.current_category in self.files:
            embed = discord.Embed(
            title="Help - " + self.current_category.replace('.json', '').capitalize(),
            description="Use the buttons below to navigate the help menu.",
            color=discord.Color.green()
            )
            current_file = self.current_category
            with open(f'bot/help/{current_file}', 'r') as file:
                data = json.loads(file.read())
            
            commands = data[0]['commands']
            for command in commands:
                if command['permission'] == 'ADMINISTRATOR':
                    continue
                command['name'] = command['name'].capitalize()
                command['description'] = command['description'].capitalize()
                embed.add_field(name=command['name'], value=command['description'], inline=False)
        else:
            embed = discord.Embed(
                title="Help",
                description="Use the buttons below to navigate the help menu.",
                color=discord.Color.green()
            )
        return embed
            

    @discord.ui.button(label="System", style=discord.ButtonStyle.primary)
    async def system(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_category = "system.json"
        self.is_home = False
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)
        
    @discord.ui.button(label="Sessions", style=discord.ButtonStyle.primary)
    async def help(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_category = "session.json"
        self.is_home = False
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)