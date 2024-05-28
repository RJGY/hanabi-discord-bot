import discord
from discord.ext import commands, tasks
import datetime as dt
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class SystemCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.welcome_channel = int(os.environ.get('WELCOME_CHANNEL'))
        self.general_logs = int(os.environ.get('GENERAL_LOGS'))
        self.staff_logs = int(os.environ.get('STAFF_LOGS'))
        self.guild_id = int(os.environ.get('GUILD_ID'))
        self.invites = []
        
    def find_invite_by_code(self, invite_list: list[discord.Invite], code: str) -> discord.Invite:
        for inv in invite_list:
            if inv.code == code:
                return inv
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        logging.info("Loaded invites into system_commands bot.")
        
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.nick != after.nick:
            embed = discord.Embed(
                title="Nickname Change",
                colour=discord.Colour.light_grey(),
                timestamp=dt.datetime.now()
                
            )
            embed.set_thumbnail(url=after.display_avatar)
            embed.set_author(name="Hanabi Bot")
            if not after.nick:
                embed.add_field(name=f'{before.nick} (ID: {before.id}) reset their nickname to {after.name}', value='', inline=False)
            else:
                embed.add_field(name=f'{before.name} (ID: {before.id}) changed their nickname to {after.nick}', value='', inline=False)
            await self.bot.get_channel(self.general_logs).send(embed=embed)
        if before.name != after.name:
            embed = discord.Embed(
                title="Username Change",
                colour=discord.Colour.light_grey(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=after.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{before.name} (ID: {before.id}) changed their name to {after.name}', value='', inline=False)
            await self.bot.get_channel(self.general_logs).send(embed=embed)
        if before.display_avatar != after.display_avatar:
            embed = discord.Embed(
                title="Avatar Change",
                colour=discord.Colour.light_grey(),
                timestamp=dt.datetime.now()
            )
            embed.set_thumbnail(url=after.display_avatar)
            embed.set_author(name="Hanabi Bot")
            embed.add_field(name=f'{before.name} changed their avatar.', value='', inline=False)
            await after.guild.get_channel(self.general_logs).send(embed=embed)
        if before.roles != after.roles:
            added_roles = [elem for elem in after.roles if elem not in before.roles]
            removed_roles = [elem for elem in before.roles if elem not in after.roles]
            embed = discord.Embed(
                title="Role Change",
                colour=discord.Colour.light_grey(),
                timestamp=dt.datetime.now()
                
            )
            embed.set_thumbnail(url=after.display_avatar)
            embed.set_author(name="Hanabi Bot")
            if added_roles:
                roles_list = [elem.name for elem in added_roles]
                roles_string = ", ".join(roles_list)
                embed.add_field(name=f'Added roles:', value=roles_string, inline=False)
            if removed_roles:
                roles_list = [elem.name for elem in removed_roles]
                roles_string = ", ".join(roles_list)
                embed.add_field(name=f'Removed roles:', value=roles_string, inline=False)
            # TODO: Method should be either through bot or Manual if done via discord.
            await self.bot.get_channel(self.general_logs).send(embed=embed)
            
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = discord.Embed(
            title="Member Joined",
            colour=discord.Colour.light_grey(),
            timestamp=dt.datetime.now()
            
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name="Hanabi Bot")
        
        invites_before_join = self.invites
        invites_after_join = await member.guild.invites()
        
        for invite in invites_before_join:
            if invite.uses < self.find_invite_by_code(invites_after_join, invite.code).uses:
                embed.add_field(name=f'{member.name} joined via Invite Code {invite.code}', value=f'Invited by {invite.inviter}', inline=False)

        await self.bot.get_channel(self.general_logs).send(embed=embed)
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = discord.Embed(
            title="Member Left",
            colour=discord.Colour.light_grey(),
            timestamp=dt.datetime.now()
            
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'{member.name} left the server.', value='')

        await self.bot.get_channel(self.general_logs).send(embed=embed)
        self.invites = await self.bot.get_guild(self.guild_id).invites()
            
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        embed = discord.Embed(
            title="Invite Created",
            colour=discord.Colour.light_grey(),
            timestamp=dt.datetime.now()
        )
        embed.set_thumbnail(url=invite.inviter.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'{invite.inviter.name} created an invite.', value=f'ID: {invite.code}', inline=False)

        await self.bot.get_channel(self.general_logs).send(embed=embed)
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        self.invites = await self.bot.get_guild(self.guild_id).invites()
        
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot:
            return
        
        embed = discord.Embed(
            title="Message Editted",
            colour=discord.Colour.light_grey(),
            timestamp=dt.datetime.now()
            
        )
        embed.set_thumbnail(url=before.author.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'{before.author.name} editted a message.', value='', inline=False)
        embed.add_field(name=f'Old Message:', value=f'{before.content}', inline=False)
        embed.add_field(name=f'New Message:', value=f'{after.content}', inline=False)

        await self.bot.get_channel(self.general_logs).send(embed=embed)
        
    @commands.Cog.listener()
    async def on_message_delete(self, before: discord.Message):
        if before.author.bot:
            return
        
        embed = discord.Embed(
            title="Message Deleted",
            colour=discord.Colour.light_grey(),
            timestamp=dt.datetime.now()
            
        )
        embed.set_thumbnail(url=before.author.display_avatar)
        embed.set_author(name="Hanabi Bot")
        embed.add_field(name=f'{before.author.name} deleted a message.', value='', inline=False)
        embed.add_field(name=f'Old Message:', value=f'{before.content}', inline=False)

        await self.bot.get_channel(self.general_logs).send(embed=embed)
    

async def setup(bot: commands.Bot):
    await bot.add_cog(SystemCommands(bot))
    

if __name__ == "__main__":
    pass