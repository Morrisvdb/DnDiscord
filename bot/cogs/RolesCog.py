import discord
from discord.ext import commands
from discord import guild_only
from models import Role
from __init__ import db

class RolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    rolescommands_group = discord.SlashCommandGroup(name="roles", help="Commands for managing roles")
    
    @rolescommands_group.command(name="add", help="Add a role to the server")
    @guild_only()
    @commands.has_permissions(manage_roles=True)
    async def add_role(self, ctx, role: discord.Role):
        role_exists = db.query(Role).filter_by(role_id=role.id, guild_id=ctx.guild.id).first()
        if role_exists is not None:
            alreadyAddedEmbed = discord.Embed(
                title="Role already added",
                description="This role is already added to the menu \n Use `/roles remove` to remove it",
                color=discord.Color.orange()
            )
            await ctx.respond(embed=alreadyAddedEmbed)
            return
        
        successEmbed = discord.Embed(
            title="Role added",
            description=f"{role.name} has been added to the menu",
            color=discord.Color.green()
        )
        await ctx.respond(embed=successEmbed)
        
        newRole = Role(role_id=role.id, guild_id=ctx.guild.id)
        db.add(newRole)
        db.commit()
        
    @rolescommands_group.command(name="remove", help="Remove a role from the server")
    @guild_only()
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, ctx, role: discord.Role):
        role = db.query(Role).filter_by(role_id=role.id, guild_id=ctx.guild.id).first()
        if not role:
            roleNotFoundEmbed = discord.Embed(
                title="Role not found",
                description="This role is not in the menu. \n Use `/roles add` to add it",
                color=discord.Color.red()
            )
            await ctx.respond(embed=roleNotFoundEmbed)
            return
        
        successEmbed = discord.Embed(
            title="Role removed",
            description=f"Role has been removed from the menu",
            color=discord.Color.green()
        )
        await ctx.respond(embed=successEmbed)
        
        db.delete(role)
        db.commit()
        
        
    
    
def setup(bot):
    bot.add_cog(RolesCog(bot))