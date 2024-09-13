import discord

class RoleSelectView(discord.ui.View):
    def __init__(self, roles):
        super().__init__(timeout=None)
        self.roles = roles
        
        self.set_roles()
        
        
    def set_roles(self):
        select_roles = []
        for role in self.roles:
            select_roles.append(discord.SelectOption(label=role.name, value=str(role.id)))
        
        self.select_role.options = select_roles

    @discord.ui.select(placeholder="Select a role", options=[discord.SelectOption(label="No Roles Found", value="none")])
    async def select_role(self, select, interaction):
        if interaction.user.get_role(int(select.values[0])) in interaction.user.roles:
            await interaction.user.remove_roles(discord.utils.get(interaction.guild.roles, id=int(select.values[0])))
            await interaction.response.send_message("Role Removed!", ephemeral=True)
        else:
            await interaction.user.add_roles(discord.utils.get(interaction.guild.roles, id=int(select.values[0])))
            await interaction.response.send_message("Role Added!", ephemeral=True)
        
        self.set_roles()